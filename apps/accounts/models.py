from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    registration_ip = models.GenericIPAddressField(null=True, blank=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )
    dni = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True
    )
    KYC_STATUS_CHOICES = [
        ("PENDING_VERIFICATION", "Pending Verification"),
        ("VERIFIED", "Verified"),
        ("REJECTED", "Rejected"),
        ("BLOCKED", "Blocked"),
    ]
    kyc_status = models.CharField(
        max_length=25,
        choices=KYC_STATUS_CHOICES,
        default="PENDING_VERIFICATION"
    )

    def __str__(self):
        return f"Profile of {self.user.username} - {self.kyc_status}"


class SuspiciousActivity(models.Model):
    class TriggerType(models.TextChoices):
        MULTI_ACCOUNT_IP = 'MULTI_ACCOUNT_IP', 'Múltiples cuentas desde misma IP'
        IDENTICAL_BETS = 'SAME_BETS', 'Patrones de apuestas idénticas'
        VELOCITY_WITHDRAW = 'VEL_WITHDRAW', 'Retiro inmediato post-recarga'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='accounts_suspicious_activities'
    )
    trigger_type = models.CharField(max_length=30, choices=TriggerType.choices)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Alerta {self.trigger_type} - {self.user.username}"


# Signal: crear cuenta WALLET automáticamente al crear un usuario
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def crear_wallet_automatico(sender, instance, created, **kwargs):
    if created:
        try:
            from apps.wallet.models import Account
            Account.objects.get_or_create(
                user=instance,
                type=Account.AccountType.WALLET,
                defaults={'currency': 'PEN'},
            )
        except Exception:
            pass