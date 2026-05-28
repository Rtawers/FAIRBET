from decimal import Decimal, InvalidOperation
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from apps.events.models import Event, Market
from apps.events.services import update_odds, suspend_market, reopen_market
from apps.events.serializers import EventSerializer, MarketSerializer, SelectionSerializer


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.prefetch_related("markets__selections").all()
    serializer_class = EventSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy", "transition"]:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    @action(detail=True, methods=["post"])
    def transition(self, request, pk=None):
        event = self.get_object()
        new_status = request.data.get("status")
        if not new_status:
            return Response({"detail": "Se requiere 'status'."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            event.transition_to(new_status)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(EventSerializer(event).data)


class MarketViewSet(viewsets.ModelViewSet):
    queryset = Market.objects.select_related("event").prefetch_related("selections").all()
    serializer_class = MarketSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    @action(detail=True, methods=["post"], url_path="odds")
    def update_odds_action(self, request, pk=None):
        market = self.get_object()
        outcome = request.data.get("outcome")
        raw_odds = request.data.get("odds")
        if not outcome or raw_odds is None:
            return Response({"detail": "Se requieren 'outcome' y 'odds'."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            new_odds = Decimal(str(raw_odds))
        except InvalidOperation:
            return Response({"detail": "Valor de odds inválido."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            selection = market.selections.get(outcome=outcome)
            update_odds(selection, new_odds=new_odds, changed_by=request.user)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(SelectionSerializer(selection).data)

    @action(detail=True, methods=["post"])
    def suspend(self, request, pk=None):
        market = self.get_object()
        suspend_market(market)
        return Response(MarketSerializer(market).data)

    @action(detail=True, methods=["post"])
    def reopen(self, request, pk=None):
        market = self.get_object()
        try:
            reopen_market(market)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(MarketSerializer(market).data)