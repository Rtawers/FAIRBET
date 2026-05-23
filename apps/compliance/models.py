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
        """Verifica si la exclusión está vigente en el momento actual."""
        now = timezone.now()
        if self.end_date is None:
            return True # Indefinida
        return now <= self.end_date

    class Meta:
        ordering = ['-created_at']