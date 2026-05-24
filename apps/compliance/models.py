from django.db import models
from django.conf import settings
from django.utils import timezone

class SelfExclusion(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='self_exclusions'
    )
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_active(self):
        now = timezone.now()
        # Indefinida: siempre activa. Temporal: activa si aún no llega la fecha de fin.
        if self.end_date is None:
            return True
        return now < self.end_date
    class Meta:
        ordering = ['-created_at']


class DepositLimit(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='depositlimit'
    )
    
    active_limit = models.DecimalField(max_digits=18, decimal_places=4)
    pending_limit = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    pending_since = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Límite de {self.user.username}: {self.active_limit}"
