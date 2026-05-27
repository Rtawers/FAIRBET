from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from apps.events.models import Selection, OddsHistory

def calculate_margin(*odds_list: Decimal) -> Decimal:
    if not odds_list:
        raise ValueError("Se necesita al menos una cuota.")
    total = sum(Decimal("1") / odd for odd in odds_list)
    margin = (total - Decimal("1")) * Decimal("100")
    return margin.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)



def update_odds(selection: Selection, new_odds: Decimal, changed_by=None) -> Selection:
    if new_odds <= Decimal("1.00"):
        raise ValueError(f"Las odds deben ser > 1.00. Recibido: {new_odds}")

    with transaction.atomic():
        OddsHistory.objects.create(
            selection=selection,
            odds_before=selection.odds,
            odds_after=new_odds,
            changed_by=changed_by,
        )
        Selection.objects.filter(pk=selection.pk).update(odds=new_odds)
        selection.odds = new_odds

    _broadcast_odds_update(selection)
    return selection


def _broadcast_odds_update(selection: Selection) -> None:
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        if channel_layer is None:
            return
        group_name = f"event_{selection.market.event_id}_odds"
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type":         "odds.update",
                "selection_id": selection.pk,
                "outcome":      selection.outcome,
                "odds":         str(selection.odds),
                "market_id":    selection.market_id,
            },
        )
    except Exception:
        pass

def suspend_market(market):
    from apps.events.models import MarketStatus
    market.status = MarketStatus.SUSPENDED
    market.save(update_fields=["status", "updated_at"])
    return market


def reopen_market(market):
    from apps.events.models import MarketStatus
    if market.status != MarketStatus.SUSPENDED:
        raise ValueError(
            f"Solo se puede reabrir un mercado SUSPENDED. Estado actual: {market.status}"
        )
    market.status = MarketStatus.OPEN
    market.save(update_fields=["status", "updated_at"])
    return market

def suspend_market_with_delay(market, delay_seconds: int = 30):
    """
    Suspende un mercado y programa su reapertura automática
    después de delay_seconds segundos vía Celery.
    """
    from apps.events.tasks import reopen_market_after_delay
    suspend_market(market)
    reopen_market_after_delay.apply_async(
        args=[market.pk],
        countdown=delay_seconds,
    )
    return market