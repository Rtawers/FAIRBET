import datetime
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.compliance.models import SelfExclusion
from apps.compliance.services import apply_self_exclusion

User = get_user_model()

class SelfExclusionTests(TestCase):
    def setUp(self):
        # Creamos un usuario de prueba usando el modelo de usuario por defecto de Django
        self.user = User.objects.create(username="test_user")

    def test_1_autoexclusion_temporal_7_dias_calcula_fecha_fin(self):
        """1 Autoexclusión temporal 7 días calcula fecha fin correcta RED → GREEN"""
        exclusion = apply_self_exclusion(user=self.user, duration_days=7)
        self.assertIsNotNone(exclusion.end_date)
        expected_end_date = (timezone.now() + datetime.timedelta(days=7)).date()
        self.assertEqual(exclusion.end_date.date(), expected_end_date)

    def test_2_autoexclusion_indefinida_no_tiene_fecha_fin(self):
        """2 Autoexclusión indefinida no tiene fecha fin RED → GREEN"""
        exclusion = apply_self_exclusion(user=self.user, duration_days=None)
        self.assertIsNone(exclusion.end_date)
        self.assertTrue(exclusion.is_active())