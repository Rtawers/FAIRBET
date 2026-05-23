from django.db import models  # noqa: F401

# Modelos: AuditLog append-only encadenado por hash (SHA256(hash_n-1 + payload)).
