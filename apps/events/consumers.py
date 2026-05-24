import json
from channels.generic.websocket import AsyncWebsocketConsumer


class OddsConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.event_id = self.scope["url_route"]["kwargs"]["event_id"]
        self.group_name = f"event_{self.event_id}_odds"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self._send_current_odds()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return
        if data.get("type") == "ping":
            await self.send(text_data=json.dumps({"type": "pong"}))

    async def odds_update(self, event):
        await self.send(text_data=json.dumps({
            "type":         "odds_update",
            "selection_id": event["selection_id"],
            "outcome":      event["outcome"],
            "odds":         event["odds"],
            "market_id":    event["market_id"],
        }))

    async def _send_current_odds(self):
        from channels.db import database_sync_to_async
        from apps.events.models import Event, MarketStatus

        @database_sync_to_async
        def get_snapshot(event_id):
            try:
                ev = Event.objects.prefetch_related("markets__selections").get(pk=event_id)
            except Event.DoesNotExist:
                return None
            result = []
            for market in ev.markets.filter(status=MarketStatus.OPEN):
                for sel in market.selections.all():
                    result.append({
                        "market_id":    market.pk,
                        "market_name":  market.name,
                        "selection_id": sel.pk,
                        "outcome":      sel.outcome,
                        "odds":         str(sel.odds),
                    })
            return result

        snapshot = await get_snapshot(self.event_id)
        if snapshot is None:
            await self.close(code=4004)
            return
        await self.send(text_data=json.dumps({
            "type":       "odds_snapshot",
            "event_id":   int(self.event_id),
            "selections": snapshot,
        }))