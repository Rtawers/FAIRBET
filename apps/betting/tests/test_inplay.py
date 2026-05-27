from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.events.models import (
    Event, Market, Selection, EventStatus, MarketStatus,
)
from apps.wallet.models import Account, Bet
from apps.wallet.services import execute_recharge
from apps.betting.services import place_bet

User = get_user_model()


class InPlayBettingTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="inplay", password="x")
        self.user.profile.dni = "99999999"
        self.user.profile.kyc_status = "VERIFIED"
        self.user.profile.save()

        Account.objects.create(type=Account.AccountType.CASA)
        Account.objects.create(type=Account.AccountType.PENDING)
        Account.objects.create(user=self.user, type=Account.AccountType.WALLET)
        execute_recharge(self.user, Decimal("100.0000"))

    def _crear_selection(self, event_status, market_status=MarketStatus.OPEN):
        evento = Event.objects.create(
            name="Final", home_team="A", away_team="B",
            starts_at=timezone.now() + timedelta(days=1),
            status=event_status,
        )
        market = Market.objects.create(
            event=evento, name="1X2", market_type="1x2",
            status=market_status,
        )
        return Selection.objects.create(
            market=market, name="Local", outcome="LOCAL", odds="2.50",
        )

    def test_apuesta_en_evento_live_es_aceptada(self):
        # In-play: evento LIVE con mercado OPEN -> se acepta
        selection = self._crear_selection(EventStatus.LIVE, MarketStatus.OPEN)
        bet = place_bet(self.user, selection, Decimal("10.0000"))
        self.assertEqual(bet.status, Bet.BetStatus.ACCEPTED)

    def test_apuesta_rechazada_si_mercado_suspendido(self):
        # In-play: evento LIVE pero mercado SUSPENDED -> se rechaza
        selection = self._crear_selection(EventStatus.LIVE, MarketStatus.SUSPENDED)
        with self.assertRaises(ValidationError):
            place_bet(self.user, selection, Decimal("10.0000"))

    def test_apuesta_rechazada_en_evento_finalizado(self):
        # Evento FINISHED -> no apostable
        selection = self._crear_selection(EventStatus.FINISHED, MarketStatus.OPEN)
        with self.assertRaises(ValidationError):
            place_bet(self.user, selection, Decimal("10.0000"))


class MercadosAdicionalesTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="mercados", password="x")
        self.user.profile.dni = "88888888"
        self.user.profile.kyc_status = "VERIFIED"
        self.user.profile.save()

        Account.objects.create(type=Account.AccountType.CASA)
        Account.objects.create(type=Account.AccountType.PENDING)
        Account.objects.create(user=self.user, type=Account.AccountType.WALLET)
        execute_recharge(self.user, Decimal("100.0000"))

        self.evento = Event.objects.create(
            name="A vs B", home_team="A", away_team="B",
            starts_at=timezone.now() + timedelta(days=1),
            status=EventStatus.SCHEDULED,
        )

    def _selection_de_mercado(self, market_type, outcome):
        market = Market.objects.create(
            event=self.evento, name=market_type, market_type=market_type,
        )
        return Selection.objects.create(
            market=market, name=outcome, outcome=outcome, odds="1.90",
        )

    def test_apuesta_sobre_mercado_overunder(self):
        # Mercado O/U se apuesta igual que 1X2 (sin lógica especial)
        selection = self._selection_de_mercado("over_under", "OVER")
        bet = place_bet(self.user, selection, Decimal("10.0000"))
        self.assertEqual(bet.status, Bet.BetStatus.ACCEPTED)

    def test_apuesta_sobre_mercado_btts(self):
        selection = self._selection_de_mercado("btts", "BTTS_YES")
        bet = place_bet(self.user, selection, Decimal("10.0000"))
        self.assertEqual(bet.status, Bet.BetStatus.ACCEPTED)