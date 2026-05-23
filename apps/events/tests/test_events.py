"""
apps/events/tests/test_events.py
TDD - escribimos los tests ANTES del código.
"""
import pytest
from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.events.models import Event, Market, Selection, EventStatus, MarketStatus


def make_event(**kwargs):
    defaults = dict(
        name="Perú vs Brasil",
        home_team="Perú",
        away_team="Brasil",
        starts_at=timezone.now() + timezone.timedelta(days=1),
    )
    defaults.update(kwargs)
    return Event.objects.create(**defaults)


# ============================================================
# TEST 1 — Event recién creado tiene estado SCHEDULED
# ============================================================

@pytest.mark.django_db
def test_event_default_status_is_scheduled():
    event = make_event()
    assert event.status == EventStatus.SCHEDULED


# ============================================================
# TEST 2 — Market recién creado tiene estado OPEN
# ============================================================

@pytest.mark.django_db
def test_market_default_status_is_open():
    event = make_event()
    market = Market.objects.create(
        event=event,
        name="1X2",
        market_type="1x2_test",
    )
    assert market.status == MarketStatus.OPEN


@pytest.mark.django_db
def test_create_1x2_market_creates_three_selections():
    event = make_event()
    market = Market.create_1x2_market(
        event=event,
        odds_home=Decimal("2.50"),
        odds_draw=Decimal("3.20"),
        odds_away=Decimal("2.80"),
    )
    assert market.selections.count() == 3
    outcomes = set(market.selections.values_list("outcome", flat=True))
    assert outcomes == {"LOCAL", "DRAW", "AWAY"}


@pytest.mark.django_db
def test_create_1x2_market_is_atomic():
    event = make_event()
    count_before = Market.objects.count()
    with pytest.raises(Exception):
        Market.create_1x2_market(
            event=event,
            odds_home=Decimal("2.50"),
            odds_draw=Decimal("3.20"),
            odds_away=Decimal("0.50"),  # inválido → rollback
        )
    assert Market.objects.count() == count_before

@pytest.mark.django_db
def test_cannot_create_market_on_voided_event():
    event = make_event(status=EventStatus.VOIDED)
    with pytest.raises(ValueError, match="anulado"):
        Market.create_1x2_market(
            event=event,
            odds_home=Decimal("2.50"),
            odds_draw=Decimal("3.20"),
            odds_away=Decimal("2.80"),
        )