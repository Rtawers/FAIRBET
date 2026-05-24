import hashlib
from .models import AuditLog

def calculate_hash(previous_hash, payload):
    # 1. Concatenar el hash anterior con el payload en una sola cadena
    data = previous_hash + payload

    # 2. Calcular el SHA256 de esa cadena (convertida a bytes) y devolver el hex
    return hashlib.sha256(data.encode()).hexdigest()

def verify_chain():
    # Recorrer todos los registros en orden cronológico
    for log in AuditLog.objects.all().order_by("created_at"):
        # Recalcular el hash de este registro con sus datos guardados
        recalculated = calculate_hash(log.previous_hash, log.payload)
        # Si no coincide con el guardado, la cadena está rota
        if recalculated != log.current_hash:
            return False
    # Si todos coincidieron, la cadena está íntegra
    return True

def create_audit_log(payload):
    # Buscar el último eslabón de la cadena (la BD es la fuente de verdad)
    last = AuditLog.objects.order_by("created_at").last()
    previous_hash = last.current_hash if last else "0" * 64  # génesis si no hay ninguno

    # Calcular el hash de este registro encadenándolo al anterior
    current_hash = calculate_hash(previous_hash, payload)

    return AuditLog.objects.create(
        payload=payload,
        previous_hash=previous_hash,
        current_hash=current_hash,
    )