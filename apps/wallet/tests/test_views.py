# apps/wallet/tests/test_views.py
"""
Fase RED — Endpoints REST del Wallet.

Tests para:
  - GET  /api/wallet/balance/   → saldo derivado del usuario
  - POST /api/wallet/recharge/  → recarga con idempotency key
  - POST /api/wallet/withdraw/  → retiro simulado
"""
from decimal import Decimal

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken


class WalletEndpointsTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='test_api', password='pass123'
        )
        from apps.wallet.models import Account
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
        # JWT token para autenticacion
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )

    def test_balance_returns_current_balance(self):
        """GET /api/wallet/balance/ retorna el saldo actual del usuario."""
        from apps.wallet.services import execute_recharge
        execute_recharge(user=self.user, amount=Decimal('100.0000'))

        url = reverse('wallet:balance')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('balance', response.data)
        self.assertEqual(
            Decimal(str(response.data['balance'])),
            Decimal('100.0000')
        )

    def test_balance_requires_authentication(self):
        """GET /api/wallet/balance/ sin token retorna 401."""
        self.client.credentials()
        url = reverse('wallet:balance')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_recharge_creates_transaction(self):
        """POST /api/wallet/recharge/ crea una transaccion y retorna 201."""
        url = reverse('wallet:recharge')
        response = self.client.post(
            url,
            {'amount': '50.0000'},
            HTTP_IDEMPOTENCY_KEY='test-key-001',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('transaction_id', response.data)
        self.assertIn('balance', response.data)

    def test_recharge_requires_idempotency_key(self):
        """POST /api/wallet/recharge/ sin Idempotency-Key retorna 400."""
        url = reverse('wallet:recharge')
        response = self.client.post(url, {'amount': '50.0000'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_recharge_is_idempotent(self):
        """Dos recargas con el mismo Idempotency-Key solo ejecutan una."""
        url = reverse('wallet:recharge')
        data = {'amount': '50.0000'}
        key = 'idempotent-key-001'

        response1 = self.client.post(url, data, HTTP_IDEMPOTENCY_KEY=key)
        response2 = self.client.post(url, data, HTTP_IDEMPOTENCY_KEY=key)

        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response1.data['transaction_id'],
            response2.data['transaction_id'],
        )

    def test_recharge_rejects_invalid_amount(self):
        """POST /api/wallet/recharge/ con monto <= 0 retorna 400."""
        url = reverse('wallet:recharge')
        response = self.client.post(
            url,
            {'amount': '-10'},
            HTTP_IDEMPOTENCY_KEY='test-key-002',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_withdraw_reduces_balance(self):
        """POST /api/wallet/withdraw/ reduce el saldo del usuario."""
        from apps.wallet.services import execute_recharge
        execute_recharge(user=self.user, amount=Decimal('100.0000'))

        url = reverse('wallet:withdraw')
        response = self.client.post(
            url,
            {'amount': '30.0000'},
            HTTP_IDEMPOTENCY_KEY='withdraw-key-001',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Decimal(str(response.data['balance'])),
            Decimal('70.0000')
        )

    def test_withdraw_rejects_insufficient_funds(self):
        """POST /api/wallet/withdraw/ sin saldo suficiente retorna 400."""
        url = reverse('wallet:withdraw')
        response = self.client.post(
            url,
            {'amount': '999.0000'},
            HTTP_IDEMPOTENCY_KEY='withdraw-key-002',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)