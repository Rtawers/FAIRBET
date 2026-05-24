
from django.test import TestCase
from apps.audit.services import calculate_hash
from apps.audit.models import AuditLog 
from apps.audit.services import calculate_hash, verify_chain 

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