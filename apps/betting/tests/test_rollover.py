from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal

from apps.wallet.models import Account, Bet, Transaction, LedgerEntry
from apps.wallet.services import execute_recharge, execute_bet_lock
from apps.betting.rollover_service import rollover_cumplido

User = get_user_model()


class RolloverTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="bonero", password="x")
        self.user.profile.kyc_status = "VERIFIED"
        self.user.profile.save()

        Account.objects.create(type=Account.AccountType.CASA)
        Account.objects.create(type=Account.AccountType.PENDING)
        Account.objects.create(user=self.user, type=Account.AccountType.WALLET)
        # Cuenta BONUS con bono de 20 -> rollover requerido = 20 x 5 = 100
        self.bonus = Account.objects.create(
            user=self.user, type=Account.AccountType.BONUS
        )
        # Acreditamos el bono manualmente para el test (Lennart hará el servicio real)
        self._acreditar_bono(Decimal("20.0000"))

        execute_recharge(self.user, Decimal("500.0000"))

    def _acreditar_bono(self, monto):
        # Helper de test: simula la acreditación del bono a la cuenta BONUS
        tx = Transaction.objects.create(kind=Transaction.Kind.RECHARGE)
        LedgerEntry.objects.create(
            transaction=tx, account=self.bonus,
            amount=monto, direction=LedgerEntry.Direction.CREDIT,
        )

    def _apostar(self, monto, status=Bet.BetStatus.ACCEPTED):
        lock_tx = execute_bet_lock(self.user, monto)
        return Bet.objects.create(
            user=self.user, amount=monto, odds=Decimal("2.00"),
            lock_transaction=lock_tx, status=status,
        )

    def test_rollover_no_cumplido_si_aposto_menos_de_5x(self):
        # Bono 20 -> requiere apostar 100. Apuesta solo 50.
        self._apostar(Decimal("50.0000"))
        self.assertFalse(rollover_cumplido(self.user))

    def test_rollover_cumplido_si_aposto_5x_o_mas(self):
        # Bono 20 -> requiere 100. Apuesta 100 (en dos apuestas de 50).
        self._apostar(Decimal("50.0000"))
        self._apostar(Decimal("50.0000"))
        self.assertTrue(rollover_cumplido(self.user))

    def test_apuestas_canceladas_no_cuentan_para_rollover(self):
        # Apuesta 100 pero CANCELADA -> no cuenta -> rollover NO cumplido
        self._apostar(Decimal("100.0000"), status=Bet.BetStatus.CANCELLED)
        self.assertFalse(rollover_cumplido(self.user))

    def test_sin_bono_no_hay_restriccion(self):
        # Usuario sin bono -> rollover siempre cumplido (nada que liberar)
        otro = User.objects.create_user(username="sinbono", password="x")
        otro.profile.kyc_status = "VERIFIED"
        otro.profile.save()
        self.assertTrue(rollover_cumplido(otro))