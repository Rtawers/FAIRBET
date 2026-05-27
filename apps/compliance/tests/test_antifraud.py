from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.compliance.models import SuspiciousActivity
from apps.compliance.services import check_transaction_velocity
from apps.wallet.services import execute_recharge
from decimal import Decimal

User = get_user_model()

class AntiFraudVelocityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="fraud_user", password="password123")

    def test_detecta_fraude_por_velocidad_con_seis_recargas(self):
        """Un usuario que realiza más de 5 recargas consecutivas activa la alerta VELOCITY RED → GREEN"""
        for _ in range(6):
            execute_recharge(user=self.user, amount=Decimal('10.0000'))
        
        check_transaction_velocity(self.user)

        alertas = SuspiciousActivity.objects.filter(user=self.user, activity_type='VELOCITY')
        
        self.assertTrue(alertas.exists(), "Debería haberse creado una alerta por alta velocidad.")
        self.assertIn("6 transacciones", alertas.first().description)