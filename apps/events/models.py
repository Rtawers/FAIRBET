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
    status      = models.CharField(
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