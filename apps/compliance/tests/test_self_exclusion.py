import datetime
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.compliance.models import SelfExclusion
from apps.compliance.services import apply_self_exclusion

User = get_user_model()

class SelfExclusionTests(TestCase):
    def setUp(self):

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

    def test_3_autoexclusion_expirada_ya_no_esta_activa(self):
        """3 Autoexclusión expirada ya no está activa RED → GREEN"""
        past_date = timezone.now() - datetime.timedelta(days=1)
        exclusion = SelfExclusion.objects.create(user=self.user, end_date=past_date)
        self.assertFalse(exclusion.is_active())

   def test_4_5_verificar_estado_autoexclusion_usuario(self):
        """4 y 5 Usuario sin/con exclusión activa retorna False/True RED → GREEN"""
        self.assertFalse(is_user_self_excluded(self.user))

        apply_self_exclusion(user=self.user, duration_days=30)
        self.assertTrue(is_user_self_excluded(self.user)) 