from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from apps.events.models import Event, Market, Selection, EventStatus, SelectionResult
from apps.betting.goleador_service import liquidar_goleador, SIN_GOLEADOR


class GoleadorExactoTestCase(TestCase):

    def setUp(self):
        self.evento = Event.objects.create(
            name="A vs B", home_team="A", away_team="B",
            starts_at=timezone.now() + timedelta(days=1),
            status=EventStatus.SCHEDULED,
        )
        self.market = Market.objects.create(
            event=self.evento, name="Goleador Exacto",
            market_type="goleador_exacto",
        )
        # Selecciones: dos jugadores + la especial "sin goleador"
        self.messi = Selection.objects.create(
            market=self.market, name="Messi", outcome="MESSI", odds="3.00"
        )
        self.suarez = Selection.objects.create(
            market=self.market, name="Suarez", outcome="SUAREZ", odds="4.00"
        )
        self.sin_gol = Selection.objects.create(
            market=self.market, name="Sin goleador", outcome=SIN_GOLEADOR, odds="6.00"
        )

    def test_gana_el_jugador_que_marco(self):
        selections = [self.messi, self.suarez, self.sin_gol]
        res = liquidar_goleador(selections, goleador_real="MESSI")

        self.assertEqual(res[self.messi.id], SelectionResult.WON)
        self.assertEqual(res[self.suarez.id], SelectionResult.LOST)
        self.assertEqual(res[self.sin_gol.id], SelectionResult.LOST)

    def test_empate_tecnico_gana_sin_goleador(self):
        # Partido 0-0: nadie marcó -> gana "sin goleador"
        selections = [self.messi, self.suarez, self.sin_gol]
        res = liquidar_goleador(selections, goleador_real=None)

        self.assertEqual(res[self.sin_gol.id], SelectionResult.WON)
        self.assertEqual(res[self.messi.id], SelectionResult.LOST)
        self.assertEqual(res[self.suarez.id], SelectionResult.LOST)