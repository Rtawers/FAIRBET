from django.urls import path
from apps.betting.views import place_bet_view, cashout_view, my_bets_view, settle_bet_view

app_name = "betting"

urlpatterns = [
    path("bets/", place_bet_view, name="place-bet"),
    path("bets/mine/", my_bets_view, name="my-bets"),
    path("cashout/", cashout_view, name="cashout"),
    path("settle/", settle_bet_view, name="settle_bet"),
]