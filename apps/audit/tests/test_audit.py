
from django.test import TestCase
from apps.audit.services import calculate_hash


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