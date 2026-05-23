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
        # 🔴 RED: sin validación de VOIDED
        with transaction.atomic():
            market = cls.objects.create(event=event, name="1X2", market_type="1x2")
            Selection.objects.create(market=market, name="Local",     outcome="LOCAL", odds=odds_home)
            Selection.objects.create(market=market, name="Empate",    outcome="DRAW",  odds=odds_draw)
            Selection.objects.create(market=market, name="Visitante", outcome="AWAY",  odds=odds_away)
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