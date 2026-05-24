from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied

from apps.accounts.models import UserProfile
from apps.betting.services import place_bet

User = get_user_model()


class PlaceBetKycTestCase(TestCase):
    def test_1_usuario_kyc_no_verificado_no_puede_apostar(self):
        # ARRANGE: usuario con KYC PENDING (no verificado)
        user = User.objects.create_user(username="daniel", password="x")
        UserProfile.objects.create(user=user, dni="12345678")
        # por defecto el kyc_status es PENDING_VERIFICATION

        # ACT + ASSERT: apostar debe lanzar PermissionDenied
        with self.assertRaises(PermissionDenied):
            place_bet(user)