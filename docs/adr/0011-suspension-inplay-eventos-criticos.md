# ADR-0011: Suspensión automática de mercado en eventos críticos (in-play)

## Contexto
Durante un partido en vivo, ciertos eventos críticos (gol, expulsión,
penalti) hacen que las cuotas cambien drásticamente en segundos. Si el
sistema sigue aceptando apuestas durante esos instantes, los apostadores
con información privilegiada pueden aprovecharse antes de que las cuotas
se actualicen. El reto exige suspender automáticamente los mercados por
N segundos cuando ocurre un evento crítico.

## Opciones consideradas

1. **Suspensión manual por el admin** — el operador suspende el mercado
   manualmente cuando detecta un evento crítico.
   - Pro: simple, sin lógica adicional.
   - Contra: lento — el humano reacciona en segundos, tiempo suficiente
     para que apostadores malintencionados actúen. No escala.

2. **Suspensión por webhook externo** — un proveedor de datos deportivos
   envía un evento al sistema cuando ocurre un gol o expulsión.
   - Pro: datos en tiempo real precisos.
   - Contra: dependencia externa costosa. Fuera del alcance del reto
     (plataforma educativa con datos mock).

3. **Suspensión automática vía Celery task con timeout configurable** ✓
   — cuando el admin marca un evento crítico, se suspende el mercado
   inmediatamente y se programa una tarea Celery para reabrirlo
   después de N segundos.
   - Pro: autónomo, sin dependencias externas. N es configurable.
     El canal WebSocket notifica a los clientes del cambio de estado.
   - Contra: si el worker de Celery cae, el mercado puede quedar
     suspendido indefinidamente.

## Decision
**Suspensión automática vía Celery task con timeout configurable.**

Combina inmediatez (suspensión síncrona en la misma request) con
reapertura automática (Celery la maneja sin intervención humana).
El tiempo N se define como `MARKET_SUSPENSION_SECONDS` con valor
por defecto de 30 segundos.

Flujo:
1. Admin POST /api/events/markets/{id}/suspend/
2. `suspend_market()` cambia estado a SUSPENDED
3. WebSocket broadcast notifica a clientes
4. Celery task `reopen_market_after_delay.apply_async(countdown=N)`
5. Al vencer el timer, `reopen_market()` cambia estado a OPEN
6. WebSocket broadcast notifica a clientes

## Consecuencias
Más fácil:
- N es configurable sin redeploy.
- Los clientes reciben notificación inmediata vía WebSocket.
- La lógica de suspensión ya existe en `services.py`.

Más difícil:
- Si el worker Celery cae, el mercado queda bloqueado.
- En producción real N varía por tipo de evento.

Deuda técnica:
- No implementamos distinción por tipo de evento crítico.
- La suspensión de múltiples mercados simultáneos requiere
  una transaction atómica que aún no está implementada.

## Fecha y autor
2026-05-26 - LuviMontes-P