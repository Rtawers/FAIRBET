"""
apps/events/tests/test_events.py
TDD - escribimos los tests ANTES del código.
"""
import pytest
from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.events.models import Event, Market, Selection, EventStatus, MarketStatus
from hypothesis import given, settings as h_settings
from hypothesis import strategies as st
from apps.events.services import calculate_margin


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
@pytest.mark.django_db
def test_odds_below_one_are_rejected():
    event = make_event()
    market = Market.objects.create(
        event=event, name="1X2", market_type="test_inv"
    )
    with pytest.raises(ValidationError):
        Selection.objects.create(
            market=market, name="Local",
            outcome="LOCAL", odds=Decimal("0.90"),
        )


@pytest.mark.django_db
def test_odds_equal_to_one_are_rejected():
    event = make_event()
    market = Market.objects.create(
        event=event, name="1X2", market_type="test_one"
    )
    with pytest.raises(ValidationError):
        Selection.objects.create(
            market=market, name="Local",
            outcome="LOCAL", odds=Decimal("1.00"),
        )


@pytest.mark.django_db
def test_odds_above_one_are_accepted():
    event = make_event()
    market = Market.objects.create(
        event=event, name="1X2", market_type="test_valid"
    )
    sel = Selection.objects.create(
        market=market, name="Local",
        outcome="LOCAL", odds=Decimal("1.01"),
    )
    assert sel.pk is not None


@given(
    h=st.decimals(min_value="1.01", max_value="20.00", places=2),
    d=st.decimals(min_value="1.01", max_value="20.00", places=2),
    a=st.decimals(min_value="1.01", max_value="20.00", places=2),
)
@h_settings(max_examples=100, deadline=2000)
def test_operator_margin_is_consistent(h, d, a):
    margin = calculate_margin(h, d, a)
    expected = (
        Decimal("1") / h +
        Decimal("1") / d +
        Decimal("1") / a -
        Decimal("1")
    ) * Decimal("100")
    expected = expected.quantize(Decimal("0.0001"))
    assert margin == expected
    assert isinstance(margin, Decimal)