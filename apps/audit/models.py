from django.db import models  # noqa: F401  # type: ignore[import]



class AuditLog(models.Model):
    payload = models.TextField()                    # los datos que se auditan
    previous_hash = models.CharField(max_length=64) # hash del registro anterior (64 = largo de SHA256 hex)
    current_hash = models.CharField(max_length=64) # su propio hash — ¿qué largo?
    created_at = models.DateTimeField(auto_now_add=True)  # da el orden de la cadena

    class Meta:
        ordering = ["created_at"]    # ¿por qué campo ordenas la cadena cronológicamente?
    
    def __str__(self):
        return f"AuditLog #{self.pk} - {self.current_hash[:12]}..."
    