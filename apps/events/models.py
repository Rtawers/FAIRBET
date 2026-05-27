from decimal import Decimal
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils import timezone


class EventStatus(models.TextChoices):
    SCHEDULED = "SCHEDULED", "Programado"
    LIVE      = "LIVE",      "En vivo"
    FINISHED  = "FINISHED",  "Finalizado"
    SUSPENDED = "SUSPENDED", "Suspendido"
    VOIDED    = "VOIDED",    "Anulado"


class MarketStatus(models.TextChoices):
    OPEN      = "OPEN",      "Abierto"
    SUSPENDED = "SUSPENDED", "Suspendido"
    CLOSED    = "CLOSED",    "Cerrado"
    SETTLED   = "SETTLED",   "Liquidado"


class Event(models.Model):
    name      = models.CharField(max_length=200)
    sport     = models.CharField(max_length=50, default="football")
    home_team = models.CharField(max_length=100)
    away_team = models.CharField(max_length=100)
    starts_at = models.DateTimeField()
    status    = models.CharField(
        max_length=20,
        choices=EventStatus.choices,
        default=EventStatus.SCHEDULED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    VALID_TRANSITIONS = {
        EventStatus.SCHEDULED: [EventStatus.LIVE, EventStatus.SUSPENDED, EventStatus.VOIDED],
        EventStatus.LIVE:      [EventStatus.FINISHED, EventStatus.SUSPENDED, EventStatus.VOIDED],
        EventStatus.SUSPENDED: [EventStatus.LIVE, EventStatus.VOIDED],
        EventStatus.FINISHED:  [],
        EventStatus.VOIDED:    [],
    }

    def transition_to(self, new_status: str) -> None:
        allowed = self.VALID_TRANSITIONS.get(self.status, [])
        if new_status not in allowed:
            raise ValueError(
                f"Transición inválida: {self.status} → {new_status}. "
                f"Permitidas: {allowed}"
            )
        self.status = new_status
        self.save(update_fields=["status", "updated_at"])

    class Meta:
        ordering = ["starts_at"]

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} ({self.status})"


class Market(models.Model):
    event       = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="markets")
    name        = models.CharField(max_length=100)
    market_type = models.CharField(max_length=50)
    status = models.CharField(
    max_length=20,
    choices=MarketStatus.choices,
    default=MarketStatus.OPEN,
)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("event", "market_type")]

    def __str__(self):
        return f"{self.event} — {self.name} ({self.status})"

    @classmethod
    def create_1x2_market(cls, event, odds_home, odds_draw, odds_away):
        if event.status == EventStatus.VOIDED:
            raise ValueError("No se puede crear un mercado sobre un evento anulado.")
        with transaction.atomic():
            market = cls.objects.create(event=event, name="1X2", market_type="1x2")
            Selection.objects.create(market=market, name="Local",     outcome="LOCAL", odds=odds_home)
            Selection.objects.create(market=market, name="Empate",    outcome="DRAW",  odds=odds_draw)
            Selection.objects.create(market=market, name="Visitante", outcome="AWAY",  odds=odds_away)
        return market
    @classmethod
    def create_goleador_exacto_market(cls, event, jugadores, odds_sin_goleador):
        """
        Crea un mercado de goleador exacto.
        jugadores: lista de dicts con {"nombre": str, "odds": Decimal}
        Siempre incluye SIN_GOLEADOR para cubrir empate técnico (0-0).
        """
        if event.status == EventStatus.VOIDED:
            raise ValueError("No se puede crear un mercado sobre un evento anulado.")

        with transaction.atomic():
            market = cls.objects.create(
                event=event,
                name="Goleador Exacto",
                market_type="goleador_exacto",
            )
            for jugador in jugadores:
                Selection.objects.create(
                    market=market,
                    name=jugador["nombre"],
                    outcome=jugador["nombre"].upper().replace(" ", "_"),
                    odds=jugador["odds"],
                )
            Selection.objects.create(
                market=market,
                name="Sin Goleador",
                outcome="SIN_GOLEADOR",
                odds=odds_sin_goleador,
            )
        return market


class SelectionResult(models.TextChoices):
    PENDING = "PENDING", "Pendiente"
    WON     = "WON",     "Ganó"
    LOST    = "LOST",    "Perdió"
    VOID    = "VOID",    "Anulado"


class Selection(models.Model):
    market  = models.ForeignKey(Market, on_delete=models.CASCADE, related_name="selections")
    name    = models.CharField(max_length=100)
    outcome = models.CharField(max_length=50)
    odds    = models.DecimalField(max_digits=18, decimal_places=4)
    result  = models.CharField(
        max_length=10,
        choices=SelectionResult.choices,
        default=SelectionResult.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.odds is not None and self.odds <= Decimal("1.00"):
            raise ValidationError(
                {"odds": f"Las odds deben ser > 1.00. Recibido: {self.odds}"}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.market} | {self.name} @ {self.odds}"

class OddsHistory(models.Model):
    selection   = models.ForeignKey(Selection, on_delete=models.CASCADE, related_name="odds_history")
    odds_before = models.DecimalField(max_digits=18, decimal_places=4)
    odds_after  = models.DecimalField(max_digits=18, decimal_places=4)
    changed_at  = models.DateTimeField(default=timezone.now)
    changed_by  = models.ForeignKey("auth.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="odds_changes")

    class Meta:
        ordering = ["-changed_at"]