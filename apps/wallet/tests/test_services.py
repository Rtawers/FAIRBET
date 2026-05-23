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