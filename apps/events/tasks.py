from celery import shared_task


@shared_task
def reopen_market_after_delay(market_id: int):
    """
    Reabre un mercado SUSPENDED después de N segundos.
    Se programa desde suspend_market_with_delay() via apply_async(countdown=N).
    """
    from apps.events.models import Market, MarketStatus
    from apps.events.services import reopen_market

    try:
        market = Market.objects.get(pk=market_id)
        if market.status == MarketStatus.SUSPENDED:
            reopen_market(market)
    except Market.DoesNotExist:
        pass