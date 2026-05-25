
from django.test import TestCase
from apps.audit.services import calculate_hash
from apps.audit.models import AuditLog 
from apps.audit.services import calculate_hash, verify_chain 
from django.contrib.auth import get_user_model
from decimal import Decimal
from apps.wallet.models import Account, LedgerEntry, Transaction, Bet
from apps.wallet.services import execute_recharge

from rest_framework.test import APIClient

User = get_user_model()

class CalculateHashTestCase(TestCase):
    def test_13_hash_se_calcula_con_sha256(self):
        # ARRANGE: entradas conocidas
        previous_hash = "0" * 64
        payload = "test"
        expected = "38d5259f381e159893c834e2467240587fd8883d4c152bbcb8c929ed243c629a"

        # ACT: llamar a la función que vas a crear
        result = calculate_hash(previous_hash, payload)

        # ASSERT: el resultado debe ser igual al esperado
        self.assertEqual(result, expected)
    
class VerifyChainTestCase(TestCase):
    def _crear_log(self, previous_hash, payload):
        """Helper: crea un AuditLog correctamente encadenado."""
        current = calculate_hash(previous_hash, payload)
        return AuditLog.objects.create(
            previous_hash=previous_hash,
            payload=payload,
            current_hash=current,        # pista: el hash que acabas de calcular -> current
        )

    def test_15_cadena_integra_retorna_true(self):
        # ARRANGE: crear 2 logs bien encadenados
        log1 = self._crear_log("0" * 64, "evento_1")   # génesis
        log2 = self._crear_log(log1.current_hash, "evento_2")  # apunta al hash de log1

        # ACT + ASSERT: la cadena debe estar íntegra
        self.assertTrue(verify_chain())         # pista: verify_chain()

    def test_14_modificar_log_rompe_cadena(self):
        # ARRANGE: crear 2 logs bien encadenados
        log1 = self._crear_log("0" * 64, "evento_1")
        log2 = self._crear_log(log1.current_hash, "evento_2")

        # ACT: corromper el payload de log1 SIN recalcular su hash
        log1.payload = "evento_MODIFICADO"
        log1.save()

        # ASSERT: la cadena debe detectarse como rota
        self.assertFalse(verify_chain())        # pista: verify_chain()
class AutoAuditTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="audit", password="x")
        Account.objects.create(type=Account.AccountType.CASA)
        Account.objects.create(type=Account.AccountType.PENDING)
        Account.objects.create(user=self.user, type=Account.AccountType.WALLET)

    def test_11_cada_ledgerentry_crea_auditlog(self):
        # ARRANGE: contar audit logs antes
        antes = AuditLog.objects.count()

        # ACT: una recarga crea 2 LedgerEntries (CASA debit + WALLET credit)
        execute_recharge(self.user, Decimal("50.0000"))

        # ASSERT: deben haberse creado 2 AuditLog nuevos (uno por cada LedgerEntry)
        despues = AuditLog.objects.count()
        self.assertEqual(despues - antes, 2)

    def test_12_cada_bet_crea_auditlog(self):
        # ARRANGE
        execute_recharge(self.user, Decimal("100.0000"))
        tx = Transaction.objects.create(kind=Transaction.Kind.BET_LOCK)
        antes = AuditLog.objects.count()

        # ACT: crear una Bet
        Bet.objects.create(
            user=self.user, amount=Decimal("10.0000"), odds=Decimal("2.0"),
            lock_transaction=tx,
        )

        # ASSERT: se creó al menos 1 AuditLog por la Bet
        self.assertEqual(AuditLog.objects.count() - antes, 1)

#--------------------Test Endpoint---------------------------------------------------

class VerifyChainEndpointTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Usuario admin (is_staff=True es lo que IsAdminUser valida)
        self.admin = User.objects.create_user(
            username="admin", password="x", is_staff=True
        )

    def _crear_log(self, previous_hash, payload):
        current = calculate_hash(previous_hash, payload)
        return AuditLog.objects.create(
            previous_hash=previous_hash, payload=payload, current_hash=current,
        )

    def test_15_endpoint_verifica_cadena_integra(self):
        # ARRANGE: una cadena bien encadenada
        log1 = self._crear_log("0" * 64, "evento_1")
        self._crear_log(log1.current_hash, "evento_2")

        # Autenticar como admin
        self.client.force_authenticate(user=self.admin)

        # ACT: llamar al endpoint
        response = self.client.get("/api/audit/verify/")

        # ASSERT: responde 200 y dice que la cadena es íntegra
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["integra"])