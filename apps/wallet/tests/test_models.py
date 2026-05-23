# apps/wallet/tests/test_models.py
"""
Fase RED — Modelos base del Wallet.

Invariantes financieras que deben cumplirse SIEMPRE:
  - La suma global de debitos y creditos es cero (partida doble).
  - El saldo se calcula SUM(credits) - SUM(debits), nunca se almacena.
  - Ningun wallet termina con saldo negativo.
"""
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra.django import TestCase as HypothesisTestCase


class AccountModelTestCase(TestCase):

    def test_account_types_exist(self):
        """Las 4 cuentas del sistema existen como choices."""
        from apps.wallet.models import Account

        types = [c[0] for c in Account.AccountType.choices]
        self.assertIn('WALLET', types)
        self.assertIn('CASA', types)
        self.assertIn('PENDING', types)
        self.assertIn('BONUS', types)

    def test_account_str_is_readable(self):
        """El __str__ de Account es legible."""
        from apps.wallet.models import Account

        user = User.objects.create_user(username='test_str', password='pass')
        account = Account.objects.create(
            user=user,
            type=Account.AccountType.WALLET,
            currency='PEN',
        )
        self.assertIn('WALLET', str(account))


class LedgerInvariantTestCase(HypothesisTestCase):

    @given(
        amount=st.decimals(
            min_value=Decimal('0.01'),
            max_value=Decimal('1000.00'),
            places=4,
        )
    )
    @settings(max_examples=50)
    def test_recharge_entries_sum_to_zero(self, amount):
        """
        INVARIANTE 1: la suma firmada de debitos y creditos
        de cualquier transaccion es siempre cero.
        """
        from apps.wallet.models import Account, LedgerEntry, Transaction

        user = User.objects.create_user(
            username=f'inv1_{amount}', password='pass'
        )
        casa = Account.objects.create(
            type=Account.AccountType.CASA, currency='PEN'
        )
        wallet = Account.objects.create(
            user=user, type=Account.AccountType.WALLET, currency='PEN'
        )
        tx = Transaction.objects.create(kind=Transaction.Kind.RECHARGE)
        LedgerEntry.objects.create(
            transaction=tx, account=casa,
            amount=amount, direction=LedgerEntry.Direction.DEBIT,
        )
        LedgerEntry.objects.create(
            transaction=tx, account=wallet,
            amount=amount, direction=LedgerEntry.Direction.CREDIT,
        )

        suma = Decimal('0.0000')
        for e in tx.entries.all():
            suma += e.amount if e.direction == LedgerEntry.Direction.CREDIT else -e.amount
        self.assertEqual(suma, Decimal('0.0000'))

    @given(
        amount=st.decimals(
            min_value=Decimal('0.01'),
            max_value=Decimal('1000.00'),
            places=4,
        )
    )
    @settings(max_examples=50)
    def test_wallet_balance_never_negative(self, amount):
        """
        INVARIANTE 2: ningun wallet termina con saldo negativo
        despues de una recarga.
        """
        from apps.wallet.models import Account, LedgerEntry, Transaction
        from django.db.models import Sum, Q

        user = User.objects.create_user(
            username=f'inv2_{amount}', password='pass'
        )
        casa = Account.objects.create(
            type=Account.AccountType.CASA, currency='PEN'
        )
        wallet = Account.objects.create(
            user=user, type=Account.AccountType.WALLET, currency='PEN'
        )
        tx = Transaction.objects.create(kind=Transaction.Kind.RECHARGE)
        LedgerEntry.objects.create(
            transaction=tx, account=casa,
            amount=amount, direction=LedgerEntry.Direction.DEBIT,
        )
        LedgerEntry.objects.create(
            transaction=tx, account=wallet,
            amount=amount, direction=LedgerEntry.Direction.CREDIT,
        )

        bal = LedgerEntry.objects.filter(account=wallet).aggregate(
            credits=Sum('amount', filter=Q(direction=LedgerEntry.Direction.CREDIT)),
            debits=Sum('amount', filter=Q(direction=LedgerEntry.Direction.DEBIT)),
        )
        saldo = (bal['credits'] or Decimal('0')) - (bal['debits'] or Decimal('0'))
        self.assertGreaterEqual(saldo, Decimal('0.0000'))