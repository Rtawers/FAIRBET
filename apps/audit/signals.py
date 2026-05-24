from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.wallet.models import LedgerEntry, Bet
from apps.audit.services import create_audit_log


@receiver(post_save, sender=LedgerEntry)
def audit_ledger_entry(sender, instance, created, **kwargs):
    if created:  # solo al crear, no al actualizar
        create_audit_log(f"LedgerEntry:{instance.pk}:{instance.direction}:{instance.amount}")


@receiver(post_save, sender=Bet)
def audit_bet(sender, instance, created, **kwargs):
    if created:
        create_audit_log(f"Bet:{instance.pk}:{instance.status}:{instance.amount}")