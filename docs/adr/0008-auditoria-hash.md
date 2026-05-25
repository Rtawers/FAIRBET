# ADR-0008: Auditoría inmutable con hash encadenado

## Contexto
(Necesitábamos un registro de auditoría que no se pueda alterar sin que
se note, para trazabilidad regulatoria (Ley 31557). Cada movimiento de wallet y
cada apuesta debe quedar registrado de forma verificable e inmutable.)

## Opciones consideradas
1. **Hash encadenado tipo blockchain**: cada registro incluye el hash del anterior.
   - Pros: (cualquier modificación de un registro viejo rompe la cadena → detectable)
   - Contras: (un poco más de cómputo al verificar)
2. **Tabla append-only simple, sin encadenamiento**:
   - Pros: (más simple de implementar)
   - Contras: (si alguien modifica un registro viejo en la BD, no hay forma de detectarlo)

## Decisión
(Elegimos el hash encadenado: hash_n = SHA256(hash_n-1 + payload_n). El primer
registro usa un génesis de 64 ceros porque no tiene anterior. El AuditLog se crea
automáticamente con señales post_save sobre LedgerEntry y Bet.)

## Consecuencias
- Más fácil: (verificar integridad con verify_chain, que recorre la cadena y recalcula)
- Más difícil / deuda técnica: (el payload es un string simple; en v2 sería JSON
  estructurado. La cadena se reconstruye siempre desde la BD, robusta ante reinicios.)

## Fecha y autor
2026-05-24 - Daniel Rodríguez (Rtawers)