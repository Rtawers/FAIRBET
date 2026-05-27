# apps/wallet/tests/test_bono.py
"""
Fase RED — Bono de bienvenida con rollover.

Tests para:
  - acreditar_bono: acredita fichas a cuenta BONUS con partida doble.
  - Retiro bloqueado si rollover no cumplido.
"""
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase


class AcreditarBonoTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='test_bono', password='pass'
        )
        from apps.wallet.models import Account
        Account.objects.create(
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

    def test_acreditar_bono_crea_cuenta_bonus(self):
        """acreditar_bono crea la cuenta BONUS si no existe."""
        from apps.wallet.services import acreditar_bono
        from apps.wallet.models import Account

        acreditar_bono(user=self.user, monto=Decimal('50.0000'))

        bonus = Account.objects.filter(
            user=self.user,
            type=Account.AccountType.BONUS,
        )
        self.assertTrue(bonus.exists())

    def test_acreditar_bono_crea_entries_balanceados(self):
        """acreditar_bono crea 2 entries que suman cero."""
        from apps.wallet.services import acreditar_bono
        from apps.wallet.models import LedgerEntry, Transaction

        tx = acreditar_bono(user=self.user, monto=Decimal('50.0000'))

        entries = tx.entries.all()
        self.assertEqual(entries.count(), 2)

        suma = Decimal('0.0000')
        for e in entries:
            suma += e.amount if e.direction == LedgerEntry.Direction.CREDIT else -e.amount
        self.assertEqual(suma, Decimal('0.0000'))

    def test_acreditar_bono_rechaza_monto_cero(self):
        """acreditar_bono rechaza monto <= 0."""
        from apps.wallet.services import acreditar_bono

        with self.assertRaises(ValueError):
            acreditar_bono(user=self.user, monto=Decimal('0.0000'))

    def test_get_monto_bono_retorna_saldo_bonus(self):
        """get_monto_bono retorna el saldo acreditado en cuenta BONUS."""
        from apps.wallet.services import acreditar_bono, get_monto_bono

        acreditar_bono(user=self.user, monto=Decimal('50.0000'))
        monto = get_monto_bono(user=self.user)

        self.assertEqual(monto, Decimal('50.0000'))

    def test_get_monto_bono_retorna_cero_sin_bono(self):
        """get_monto_bono retorna 0 si el usuario no tiene bono."""
        from apps.wallet.services import get_monto_bono

        monto = get_monto_bono(user=self.user)
        self.assertEqual(monto, Decimal('0.0000'))