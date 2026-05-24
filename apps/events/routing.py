from django.urls import re_path
from apps.events.consumers import OddsConsumer

websocket_urlpatterns = [
    re_path(r"^ws/events/(?P<event_id>\d+)/odds/$", OddsConsumer.as_asgi()),
]