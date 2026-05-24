from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError

from apps.accounts.models import UserProfile
from apps.betting.services import place_bet

from django.utils import timezone
from datetime import timedelta
from apps.events.models import Event, Market, Selection, EventStatus

User = get_user_model()


class PlaceBetKycTestCase(TestCase):
    def test_1_usuario_kyc_no_verificado_no_puede_apostar(self):
        # ARRANGE: usuario con KYC PENDING (no verificado)
        user = User.objects.create_user(username="daniel", password="x")
        UserProfile.objects.create(user=user, dni="12345678")
        # por defecto el kyc_status es PENDING_VERIFICATION

        # ACT + ASSERT: apostar debe lanzar PermissionDenied
        with self.assertRaises(PermissionDenied):
            place_bet(user, None)  # el segundo argumento no se usa en esta validación

class PlaceBetEventTestCase(TestCase):
    def setUp(self):
        # Usuario verificado (para que pase el KYC y lleguemos a la validación de evento)
        self.user = User.objects.create_user(username="ana", password="x")
        UserProfile.objects.create(user=self.user, dni="87654321", kyc_status="VERIFIED")

    def _crear_selection(self, event_status):
        evento = Event.objects.create(
            name="Final", home_team="A", away_team="B",
            starts_at=timezone.now() + timedelta(days=1),
            status=event_status,
        )
        market = Market.objects.create(event=evento, name="1X2", market_type="1x2")
        return Selection.objects.create(
            market=market, name="Local", outcome="LOCAL", odds="2.50"
        )

    def test_2_apuesta_sobre_evento_no_scheduled_es_rechazada(self):
        # ARRANGE: selección sobre un evento LIVE (ya empezó, no SCHEDULED)
        selection = self._crear_selection(EventStatus.LIVE)

        # ACT + ASSERT: apostar debe lanzar ValidationError
        with self.assertRaises(ValidationError):
            place_bet(self.user, selection)