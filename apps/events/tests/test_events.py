import pytest
from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import ValidationError
from hypothesis import given, settings as h_settings
from hypothesis import strategies as st
from decimal import Decimal, ROUND_HALF_UP
from apps.events.models import Event, Market, Selection, EventStatus, MarketStatus
from apps.events.services import calculate_margin, update_odds


def make_event(**kwargs):
    defaults = dict(
        name="Perú vs Brasil",
        home_team="Perú",
        away_team="Brasil",
        starts_at=timezone.now() + timezone.timedelta(days=1),
    )
    defaults.update(kwargs)
    return Event.objects.create(**defaults)


@pytest.mark.django_db
def test_event_default_status_is_scheduled():
    event = make_event()
    assert event.status == EventStatus.SCHEDULED


@pytest.mark.django_db
def test_market_default_status_is_open():
    event = make_event()
    market = Market.objects.create(event=event, name="1X2", market_type="1x2_test")
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
            odds_away=Decimal("0.50"),
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
    market = Market.objects.create(event=event, name="1X2", market_type="test_inv")
    with pytest.raises(ValidationError):
        Selection.objects.create(market=market, name="Local", outcome="LOCAL", odds=Decimal("0.90"))


@pytest.mark.django_db
def test_odds_equal_to_one_are_rejected():
    event = make_event()
    market = Market.objects.create(event=event, name="1X2", market_type="test_one")
    with pytest.raises(ValidationError):
        Selection.objects.create(market=market, name="Local", outcome="LOCAL", odds=Decimal("1.00"))


@pytest.mark.django_db
def test_odds_above_one_are_accepted():
    event = make_event()
    market = Market.objects.create(event=event, name="1X2", market_type="test_valid")
    sel = Selection.objects.create(market=market, name="Local", outcome="LOCAL", odds=Decimal("1.01"))
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
    expected = expected.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    assert margin == expected
    assert isinstance(margin, Decimal)

@pytest.mark.django_db
def test_update_odds_saves_history():
    event = make_event()
    market = Market.create_1x2_market(
        event=event,
        odds_home=Decimal("2.50"),
        odds_draw=Decimal("3.20"),
        odds_away=Decimal("2.80"),
    )
    selection = market.selections.get(outcome="LOCAL")
    update_odds(selection, new_odds=Decimal("2.80"))
    selection.refresh_from_db()
    assert selection.odds == Decimal("2.8000")
    history = selection.odds_history.first()
    assert history.odds_before == Decimal("2.5000")
    assert history.odds_after == Decimal("2.8000")


@pytest.mark.django_db
def test_update_odds_rejects_invalid():
    event = make_event()
    market = Market.create_1x2_market(
        event=event,
        odds_home=Decimal("2.50"),
        odds_draw=Decimal("3.20"),
        odds_away=Decimal("2.80"),
    )
    selection = market.selections.get(outcome="LOCAL")
    with pytest.raises((ValidationError, ValueError)):
        update_odds(selection, new_odds=Decimal("0.50"))


@pytest.mark.django_db
def test_event_transition_scheduled_to_live():
    event = make_event()
    event.transition_to(EventStatus.LIVE)
    event.refresh_from_db()
    assert event.status == EventStatus.LIVE


@pytest.mark.django_db
def test_event_transition_invalid_raises():
    event = make_event(status=EventStatus.FINISHED)
    with pytest.raises(ValueError, match="Transición inválida"):
        event.transition_to(EventStatus.LIVE)


@pytest.mark.django_db
def test_voided_is_terminal():
    event = make_event(status=EventStatus.VOIDED)
    with pytest.raises(ValueError):
        event.transition_to(EventStatus.LIVE)

# ============================================================
# TEST — Mercado goleador exacto
# ============================================================

@pytest.mark.django_db
def test_create_goleador_exacto_market_incluye_sin_goleador():
    event = make_event()
    jugadores = [
        {"nombre": "Messi",   "odds": Decimal("3.00")},
        {"nombre": "Suárez",  "odds": Decimal("4.00")},
        {"nombre": "Lautaro", "odds": Decimal("5.00")},
    ]
    market = Market.create_goleador_exacto_market(
        event=event,
        jugadores=jugadores,
        odds_sin_goleador=Decimal("2.50"),
    )
    assert market.market_type == "goleador_exacto"
    outcomes = set(market.selections.values_list("outcome", flat=True))
    assert "SIN_GOLEADOR" in outcomes
    assert market.selections.count() == 4


@pytest.mark.django_db
def test_create_goleador_exacto_market_es_atomico():
    event = make_event()
    count_before = Market.objects.count()
    with pytest.raises(Exception):
        Market.create_goleador_exacto_market(
            event=event,
            jugadores=[{"nombre": "Messi", "odds": Decimal("0.50")}],
            odds_sin_goleador=Decimal("2.50"),
        )
    assert Market.objects.count() == count_before


@pytest.mark.django_db
def test_create_goleador_exacto_no_permite_event_voided():
    event = make_event(status=EventStatus.VOIDED)
    with pytest.raises(ValueError, match="anulado"):
        Market.create_goleador_exacto_market(
            event=event,
            jugadores=[{"nombre": "Messi", "odds": Decimal("3.00")}],
            odds_sin_goleador=Decimal("2.50"),
        )

# ============================================================
# TEST — Suspensión automática con Celery
# ============================================================

@pytest.mark.django_db
def test_suspend_market_programa_reapertura():
    """
    Al suspender un mercado, debe quedar en estado SUSPENDED.
    La tarea Celery de reapertura se programa automáticamente.
    """
    from apps.events.tasks import reopen_market_after_delay
    from apps.events.services import suspend_market_with_delay

    event = make_event(status=EventStatus.LIVE)
    market = Market.create_1x2_market(
        event=event,
        odds_home=Decimal("2.50"),
        odds_draw=Decimal("3.20"),
        odds_away=Decimal("2.80"),
    )

    suspend_market_with_delay(market, delay_seconds=30)

    market.refresh_from_db()
    assert market.status == "SUSPENDED"


@pytest.mark.django_db
def test_reopen_market_after_delay_reabre_mercado():
    """
    La tarea Celery reopen_market_after_delay debe reabrir
    un mercado SUSPENDED.
    """
    from apps.events.tasks import reopen_market_after_delay

    event = make_event(status=EventStatus.LIVE)
    market = Market.create_1x2_market(
        event=event,
        odds_home=Decimal("2.50"),
        odds_draw=Decimal("3.20"),
        odds_away=Decimal("2.80"),
    )
    market.status = "SUSPENDED"
    market.save()

    reopen_market_after_delay(market.pk)

    market.refresh_from_db()
    assert market.status == "OPEN"