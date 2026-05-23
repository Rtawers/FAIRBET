# apps/wallet/tests/test_services.py
"""
Fase RED — Servicios del Wallet.

Pruebas para:
  - execute_recharge: recarga atomica con partida doble.
  - execute_bet_lock: bloqueo de fondos con select_for_update.
  - execute_bet_settlement: liquidacion WON/LOST con 3 y 2 entries.
"""
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra.django import TestCase as HypothesisTestCase
from django.test import TransactionTestCase


class ExecuteRechargeTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='test_recharge', password='pass'
        )
        from apps.wallet.models import Account
        self.wallet = Account.objects.create(
            user=self.user,
            type=Account.AccountType.WALLET,
            currency='PEN',
        )
        self.casa = Account.objects.create(
            type=Account.AccountType.CASA,
            currency='PEN',
        )

    def test_recharge_returns_transaction(self):
        """execute_recharge retorna una Transaction con kind=RECHARGE."""
        from apps.wallet.services import execute_recharge
        from apps.wallet.models import Transaction

        tx = execute_recharge(user=self.user, amount=Decimal('100.0000'))

        self.assertIsNotNone(tx.id)
        self.assertEqual(tx.kind, Transaction.Kind.RECHARGE)

    def test_recharge_creates_two_balanced_entries(self):
        """execute_recharge crea exactamente 2 entries que suman cero."""
        from apps.wallet.services import execute_recharge
        from apps.wallet.models import LedgerEntry

        tx = execute_recharge(user=self.user, amount=Decimal('100.0000'))

        entries = tx.entries.all()
        self.assertEqual(entries.count(), 2)

        suma = Decimal('0.0000')
        for e in entries:
            suma += e.amount if e.direction == LedgerEntry.Direction.CREDIT else -e.amount
        self.assertEqual(suma, Decimal('0.0000'))

    def test_recharge_credits_user_wallet(self):
        """execute_recharge acredita el monto correcto al WALLET del usuario."""
        from apps.wallet.services import execute_recharge
        from apps.wallet.models import LedgerEntry

        tx = execute_recharge(user=self.user, amount=Decimal('50.0000'))

        credito = tx.entries.get(
            account=self.wallet,
            direction=LedgerEntry.Direction.CREDIT,
        )
        self.assertEqual(credito.amount, Decimal('50.0000'))

    def test_recharge_rejects_zero_or_negative_amount(self):
        """execute_recharge rechaza montos <= 0."""
        from apps.wallet.services import execute_recharge

        with self.assertRaises(ValueError):
            execute_recharge(user=self.user, amount=Decimal('0.0000'))

        with self.assertRaises(ValueError):
            execute_recharge(user=self.user, amount=Decimal('-10.0000'))


class ExecuteBetLockTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='test_lock', password='pass'
        )
        from apps.wallet.models import Account
        from apps.wallet.services import execute_recharge

        self.wallet = Account.objects.create(
            user=self.user,
            type=Account.AccountType.WALLET,
            currency='PEN',
        )
        Account.objects.create(
            type=Account.AccountType.CASA, currency='PEN'
        )
        self.pending = Account.objects.create(
            type=Account.AccountType.PENDING, currency='PEN'
        )
        execute_recharge(user=self.user, amount=Decimal('200.0000'))

    def test_bet_lock_returns_transaction(self):
        """execute_bet_lock retorna una Transaction con kind=BET_LOCK."""
        from apps.wallet.services import execute_bet_lock
        from apps.wallet.models import Transaction

        tx = execute_bet_lock(user=self.user, amount=Decimal('50.0000'))

        self.assertIsNotNone(tx.id)
        self.assertEqual(tx.kind, Transaction.Kind.BET_LOCK)

    def test_bet_lock_moves_funds_to_pending(self):
        """execute_bet_lock mueve fondos de WALLET a PENDING."""
        from apps.wallet.services import execute_bet_lock
        from apps.wallet.models import LedgerEntry

        tx = execute_bet_lock(user=self.user, amount=Decimal('50.0000'))

        credito_pending = tx.entries.get(
            account=self.pending,
            direction=LedgerEntry.Direction.CREDIT,
        )
        self.assertEqual(credito_pending.amount, Decimal('50.0000'))

    def test_bet_lock_rejects_insufficient_funds(self):
        """execute_bet_lock rechaza si el saldo es insuficiente."""
        from apps.wallet.services import execute_bet_lock

        with self.assertRaises(ValueError) as ctx:
            execute_bet_lock(user=self.user, amount=Decimal('999.0000'))

        self.assertIn('saldo', str(ctx.exception).lower())


class ExecuteBetSettlementTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='test_settlement', password='pass'
        )
        from apps.wallet.models import Account
        from apps.wallet.services import execute_recharge, execute_bet_lock
        from apps.wallet.models import Transaction as Tx

        self.wallet = Account.objects.create(
            user=self.user,
            type=Account.AccountType.WALLET,
            currency='PEN',
        )
        self.casa = Account.objects.create(
            type=Account.AccountType.CASA, currency='PEN'
        )
        self.pending = Account.objects.create(
            type=Account.AccountType.PENDING, currency='PEN'
        )
        execute_recharge(user=self.user, amount=Decimal('200.0000'))
        self.lock_tx = execute_bet_lock(
            user=self.user, amount=Decimal('100.0000')
        )

    def _crear_bet(self, amount, odds):
        from apps.wallet.models import Bet
        from apps.wallet.services import execute_bet_lock
        return Bet.objects.create(
            user=self.user,
            amount=amount,
            odds=odds,
            lock_transaction=self.lock_tx,
            status=Bet.BetStatus.ACCEPTED,
        )

    def test_settlement_won_credits_payout_to_wallet(self):
        """Liquidacion WON acredita payout completo al WALLET (3 entries)."""
        from apps.wallet.services import execute_bet_settlement
        from apps.wallet.models import LedgerEntry, Bet

        bet = self._crear_bet(Decimal('100.0000'), Decimal('2.50'))
        tx = execute_bet_settlement(bet=bet, won=True)

        bet.refresh_from_db()
        self.assertEqual(bet.status, Bet.BetStatus.WON)
        self.assertEqual(tx.entries.count(), 3)

        credito = tx.entries.get(
            account=self.wallet,
            direction=LedgerEntry.Direction.CREDIT,
        )
        self.assertEqual(
            credito.amount,
            (Decimal('100.0000') * Decimal('2.50')).quantize(Decimal('0.0001'))
        )

    def test_settlement_lost_moves_stake_to_casa(self):
        """Liquidacion LOST mueve el stake de PENDING a CASA (2 entries)."""
        from apps.wallet.services import execute_bet_settlement
        from apps.wallet.models import LedgerEntry, Bet

        bet = self._crear_bet(Decimal('100.0000'), Decimal('2.50'))
        tx = execute_bet_settlement(bet=bet, won=False)

        bet.refresh_from_db()
        self.assertEqual(bet.status, Bet.BetStatus.LOST)
        self.assertEqual(tx.entries.count(), 2)

        credito_casa = tx.entries.get(
            account=self.casa,
            direction=LedgerEntry.Direction.CREDIT,
        )
        self.assertEqual(credito_casa.amount, Decimal('100.0000'))

    def test_settlement_raises_if_already_settled(self):
        """No se puede liquidar dos veces la misma apuesta."""
        from apps.wallet.services import execute_bet_settlement
        from apps.wallet.models import Bet

        bet = self._crear_bet(Decimal('100.0000'), Decimal('2.50'))
        execute_bet_settlement(bet=bet, won=True)

        with self.assertRaises(ValueError):
            execute_bet_settlement(bet=bet, won=True)


class ConcurrencyTestCase(TransactionTestCase):
    """
    Prueba de concurrencia: N peticiones simultaneas no generan doble gasto.

    Usa TransactionTestCase (no TestCase) porque los threads secundarios
    necesitan ver los datos creados en setUp. Con TestCase normal, los datos
    viven en una transaccion no commiteada que los threads no pueden ver.
    Con TransactionTestCase, cada operacion hace commit real a la BD.

    La guia exige textual: "Pruebas de concurrencia: simular N peticiones
    simultaneas y verificar que no haya doble gasto."
    """

    def setUp(self):
        from apps.wallet.models import Account
        from apps.wallet.services import execute_recharge

        self.user = User.objects.create_user(
            username='test_concurrencia', password='pass'
        )
        self.wallet = Account.objects.create(
            user=self.user,
            type=Account.AccountType.WALLET,
            currency='PEN',
        )
        Account.objects.create(
            type=Account.AccountType.CASA, currency='PEN'
        )
        Account.objects.create(
            type=Account.AccountType.PENDING, currency='PEN'
        )
        # Saldo inicial: 100 fichas
        execute_recharge(user=self.user, amount=Decimal('100.0000'))

    def test_concurrent_bet_locks_no_double_spend(self):
        """
        10 threads intentan apostar 20 fichas simultaneamente.
        Con saldo de 100, como maximo 5 deben tener exito.
        El saldo final NUNCA puede ser negativo.
        """
        import threading
        from apps.wallet.services import execute_bet_lock
        from apps.wallet.models import LedgerEntry, Account
        from django.db import connection
        from django.db.models import Sum, Q

        resultados = {'exitos': 0, 'rechazos': 0}
        lock = threading.Lock()

        def intentar_apostar():
            # Cada thread necesita su propia conexion a la BD
            connection.ensure_connection()
            try:
                execute_bet_lock(user=self.user, amount=Decimal('20.0000'))
                with lock:
                    resultados['exitos'] += 1
            except ValueError:
                with lock:
                    resultados['rechazos'] += 1
            except Exception:
                with lock:
                    resultados['rechazos'] += 1
            finally:
                connection.close()

        # Lanzar 10 threads simultaneamente
        threads = [
            threading.Thread(target=intentar_apostar)
            for _ in range(10)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verificacion 1: todos los intentos fueron procesados
        self.assertEqual(
            resultados['exitos'] + resultados['rechazos'], 10
        )

        # Verificacion 2: el saldo nunca es negativo
        wallet = Account.objects.get(
            user=self.user, type=Account.AccountType.WALLET
        )
        balance = LedgerEntry.objects.filter(account=wallet).aggregate(
            credits=Sum(
                'amount',
                filter=Q(direction=LedgerEntry.Direction.CREDIT)
            ),
            debits=Sum(
                'amount',
                filter=Q(direction=LedgerEntry.Direction.DEBIT)
            ),
        )
        saldo_final = (
            (balance['credits'] or Decimal('0')) -
            (balance['debits'] or Decimal('0'))
        )
        self.assertGreaterEqual(saldo_final, Decimal('0.0000'))

        # Verificacion 3: no se gastó más de lo que había
        fichas_bloqueadas = resultados['exitos'] * Decimal('20.0000')
        self.assertLessEqual(fichas_bloqueadas, Decimal('100.0000'))