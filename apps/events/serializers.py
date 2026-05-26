from rest_framework import serializers
from apps.events.models import Event, Market, Selection, OddsHistory


class SelectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Selection
        fields = ["id", "name", "outcome", "odds", "result"]


class OddsHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OddsHistory
        fields = ["id", "odds_before", "odds_after", "changed_at", "changed_by"]


class MarketSerializer(serializers.ModelSerializer):
    selections = SelectionSerializer(many=True, read_only=True)

    class Meta:
        model = Market
        fields = ["id", "name", "market_type", "status", "margin", "selections"]


class EventSerializer(serializers.ModelSerializer):
    markets = MarketSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = [
            "id", "name", "sport",
            "home_team", "away_team",
            "starts_at", "status", "markets",
        ]