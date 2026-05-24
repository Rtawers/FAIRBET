import pytest
from decimal import Decimal
from django.utils import timezone
from channels.testing import WebsocketCommunicator
from asgiref.sync import sync_to_async

from apps.events.models import Event, Market
from apps.events.services import update_odds


@sync_to_async
def _create_event_with_market():
    event = Event.objects.create(
        name="Test WS",
        home_team="A",
        away_team="B",
        starts_at=timezone.now() + timezone.timedelta(days=1),
    )
    market = Market.create_1x2_market(
        event=event,
        odds_home=Decimal("2.50"),
        odds_draw=Decimal("3.20"),
        odds_away=Decimal("2.80"),
    )
    return event, market


def _get_app():
    from config.asgi import application
    return application


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_consumer_connects_and_sends_snapshot():
    event, _ = await _create_event_with_market()
    communicator = WebsocketCommunicator(
        _get_app(), f"/ws/events/{event.pk}/odds/"
    )
    connected, _ = await communicator.connect()
    assert connected is True

    response = await communicator.receive_json_from(timeout=5)
    assert response["type"] == "odds_snapshot"
    assert response["event_id"] == event.pk
    assert len(response["selections"]) == 3

    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_odds_change_broadcasts_to_all_subscribers():
    event, market = await _create_event_with_market()
    app = _get_app()

    comm1 = WebsocketCommunicator(app, f"/ws/events/{event.pk}/odds/")
    comm2 = WebsocketCommunicator(app, f"/ws/events/{event.pk}/odds/")

    c1, _ = await comm1.connect()
    c2, _ = await comm2.connect()
    assert c1 is True
    assert c2 is True

    await comm1.receive_json_from(timeout=5)
    await comm2.receive_json_from(timeout=5)

    @sync_to_async
    def do_update():
        sel = market.selections.get(outcome="LOCAL")
        update_odds(sel, new_odds=Decimal("2.75"))

    await do_update()

    msg1 = await comm1.receive_json_from(timeout=5)
    msg2 = await comm2.receive_json_from(timeout=5)

    assert msg1["type"] == "odds_update"
    assert msg1["outcome"] == "LOCAL"
    assert Decimal(msg1["odds"]) == Decimal("2.75")
    assert msg2["type"] == "odds_update"

    await comm1.disconnect()
    await comm2.disconnect()