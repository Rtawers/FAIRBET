from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from rest_framework.test import APIClient

from apps.wallet.models import Account, Bet
from apps.wallet.services import (
    execute_recharge,
    execute_bet_lock,
    execute_bet_settlement,
)
from apps.dashboard.services import (
    calculate_ggr,
    calculate_exposure,
    calculate_bet_volume,
)

User = get_user_model()


class DashboardMetricsTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="jugador", password="x")
        self.user.profile.kyc_status = "VERIFIED"
        self.user.profile.save()

        # Cuentas del sistema necesarias para el ledger
        Account.objects.create(type=Account.AccountType.CASA)
        Account.objects.create(type=Account.AccountType.PENDING)
        Account.objects.create(user=self.user, type=Account.AccountType.WALLET)

        execute_recharge(self.user, Decimal("100.0000"))

    def test_ggr_refleja_apuesta_perdida(self):
        # El usuario apuesta 10 y PIERDE -> el stake va a la CASA
        lock_tx = execute_bet_lock(self.user, Decimal("10.0000"))
        bet = Bet.objects.create(
            user=self.user,
            amount=Decimal("10.0000"),
            odds=Decimal("2.00"),
            lock_transaction=lock_tx,
        )
        execute_bet_settlement(bet, won=False)

        # La casa ganó el stake de 10
        self.assertEqual(calculate_ggr(), Decimal("10.0000"))

    def test_exposure_suma_payout_de_apuestas_activas(self):
        # Apuesta ACCEPTED (viva): 10 x 2.00 = 20 de payout potencial
        lock_tx = execute_bet_lock(self.user, Decimal("10.0000"))
        Bet.objects.create(
            user=self.user,
            amount=Decimal("10.0000"),
            odds=Decimal("2.00"),
            lock_transaction=lock_tx,
        )

        self.assertEqual(calculate_exposure(), Decimal("20.0000"))

    def test_volumen_cuenta_apuestas_activas(self):
        lock_tx = execute_bet_lock(self.user, Decimal("10.0000"))
        Bet.objects.create(
            user=self.user,
            amount=Decimal("10.0000"),
            odds=Decimal("2.00"),
            lock_transaction=lock_tx,
        )

        volumen = calculate_bet_volume()
        self.assertEqual(volumen["total_apostado"], Decimal("10.0000"))
        self.assertEqual(volumen["numero_apuestas"], 1)

class DashboardEndpointTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()

        # Usuario normal (NO admin)
        self.user = User.objects.create_user(username="normal", password="x")

        # Usuario admin (operador)
        self.admin = User.objects.create_user(
            username="operador", password="x", is_staff=True
        )

    def test_endpoint_metrics_requiere_admin(self):
        # Un usuario normal NO puede ver las métricas
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/dashboard/metrics/")
        self.assertEqual(response.status_code, 403)

    def test_endpoint_metrics_devuelve_metricas_a_admin(self):
        # El operador (admin) SÍ puede
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/dashboard/metrics/")
        self.assertEqual(response.status_code, 200)
        # Las tres métricas están presentes
        self.assertIn("ggr", response.data)
        self.assertIn("exposure", response.data)
        self.assertIn("volumen", response.data)

    def test_endpoint_reporte_csv_requiere_admin(self):
        # Un usuario normal NO puede descargar el reporte
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/dashboard/report/csv/")
        self.assertEqual(response.status_code, 403)

    def test_endpoint_reporte_csv_devuelve_csv_a_admin(self):
        # El operador (admin) descarga el CSV
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/dashboard/report/csv/")

        self.assertEqual(response.status_code, 200)
        # Es un archivo CSV descargable
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("attachment", response["Content-Disposition"])
        # El contenido incluye las métricas
        contenido = response.content.decode("utf-8")
        self.assertIn("GGR", contenido)
        self.assertIn("Exposure", contenido)