from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.compliance.models import SuspiciousActivity
from apps.compliance.services import check_transaction_velocity, check_unusual_amount # <-- ¡Importante añadirlo aquí!
from apps.wallet.services import execute_recharge
from apps.wallet.models import Account
from decimal import Decimal

User = get_user_model()

class AntiFraudVelocityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="fraud_user", password="password123")

        Account.objects.create(user=self.user, type=Account.AccountType.WALLET)

        admin_user = User.objects.create_user(username="admin_casino", password="123")
        Account.objects.create(user=admin_user, type=Account.AccountType.CASA)

    def test_detecta_fraude_por_velocidad_con_seis_recargas(self):
        """Un usuario que realiza más de 5 recargas consecutivas activa la alerta"""
        for _ in range(6):
            execute_recharge(user=self.user, amount=Decimal('10.0000'))
        
        check_transaction_velocity(self.user)
        alertas = SuspiciousActivity.objects.filter(user=self.user, activity_type='VELOCITY')
        self.assertTrue(alertas.exists(), "Debería haberse creado una alerta por alta velocidad.")
        self.assertIn("6 transacciones", alertas.first().description)

class AntiFraudVarianceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="variance_user", password="password123")
        Account.objects.create(user=self.user, type=Account.AccountType.WALLET)
        
        if not Account.objects.filter(type=Account.AccountType.CASA).exists():
            admin_user = User.objects.create_user(username="admin_casa_var", password="123")
            Account.objects.create(user=admin_user, type=Account.AccountType.CASA)

    def test_monto_normal_no_genera_alerta_lectura(self):
        """Caso Normal: Una recarga que sigue el patrón promedio NO activa alertas (Solo Lectura)"""
        execute_recharge(user=self.user, amount=Decimal('20.00'))
        execute_recharge(user=self.user, amount=Decimal('20.00'))
        nueva_recarga = Decimal('30.00')
        execute_recharge(user=self.user, amount=nueva_recarga)
       
        check_unusual_amount(self.user, nueva_recarga)
       
        alertas = SuspiciousActivity.objects.filter(user=self.user, activity_type='VARIANCE')
        self.assertFalse(alertas.exists(), "Una recarga de 30 no debería generar alerta si el promedio es 20.")

    def test_monto_inusual_genera_alerta_fraudulenta_lectura(self):
        """Caso Fraudulento: Una recarga que supera el 300% del promedio ACTIVA la alerta (Solo Lectura)"""
        execute_recharge(user=self.user, amount=Decimal('10.00'))
        execute_recharge(user=self.user, amount=Decimal('10.00'))
        recarga_anomala = Decimal('100.00')
        execute_recharge(user=self.user, amount=recarga_anomala)

        check_unusual_amount(self.user, recarga_anomala)

        alertas = SuspiciousActivity.objects.filter(user=self.user, activity_type='VARIANCE')
        self.assertTrue(alertas.exists(), "La recarga anómala de 100 debió ser detectada.")
        self.assertIn("Monto inusual", alertas.first().description)