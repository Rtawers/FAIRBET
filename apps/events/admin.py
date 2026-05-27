from django.contrib import admin
from apps.events.models import Event, Market, Selection, OddsHistory

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'home_team', 'away_team', 'status', 'starts_at']
    list_filter = ['status', 'sport']
    search_fields = ['name', 'home_team', 'away_team']

@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = ['id', 'event', 'name', 'market_type', 'status']
    list_filter = ['status', 'market_type']

@admin.register(Selection)
class SelectionAdmin(admin.ModelAdmin):
    list_display = ['id', 'market', 'name', 'outcome', 'odds', 'result']
    list_filter = ['result']

@admin.register(OddsHistory)
class OddsHistoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'selection', 'odds_before', 'odds_after', 'changed_at']