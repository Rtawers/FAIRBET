import pytest
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from apps.events.models import Event, Market, EventStatus


def make_event(**kwargs):
    defaults = dict(
        name="Perú vs Brasil",
        home_team="Perú",
        away_team="Brasil",
        starts_at=timezone.now() + timezone.timedelta(days=1),
    )
    defaults.update(kwargs)
    return Event.objects.create(**defaults)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    user = User.objects.create_superuser(
        username="admin", password="admin123", email="admin@test.com"
    )
    return user


@pytest.fixture
def auth_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client

@pytest.mark.django_db
def test_list_events_returns_200(auth_client):
    make_event()
    response = auth_client.get("/api/events/events/")
    assert response.status_code == 200
    assert len(response.data) >= 1

@pytest.mark.django_db
def test_create_event_returns_201(auth_client):
    data = {
        "name": "Argentina vs Chile",
        "home_team": "Argentina",
        "away_team": "Chile",
        "starts_at": "2026-06-01T20:00:00Z",
        "sport": "football",
    }
    response = auth_client.post("/api/events/events/", data, format="json")
    assert response.status_code == 201
    assert response.data["status"] == EventStatus.SCHEDULED



@pytest.mark.django_db
def test_transition_event_to_live(auth_client):
    event = make_event()
    response = auth_client.post(
        f"/api/events/events/{event.pk}/transition/",
        {"status": "LIVE"},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["status"] == "LIVE"


@pytest.mark.django_db
def test_update_odds_via_api(auth_client):
    event = make_event()
    market = Market.create_1x2_market(
        event=event,
        odds_home=Decimal("2.50"),
        odds_draw=Decimal("3.20"),
        odds_away=Decimal("2.80"),
    )
    response = auth_client.post(
        f"/api/events/markets/{market.pk}/odds/",
        {"outcome": "LOCAL", "odds": "2.90"},
        format="json",
    )
    assert response.status_code == 200
    assert Decimal(response.data["odds"]) == Decimal("2.90")