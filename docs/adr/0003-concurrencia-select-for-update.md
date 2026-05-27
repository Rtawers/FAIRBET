# ADR-0003: Estrategia de Concurrencia — Bloqueo Pesimista

## Contexto
Multiples usuarios pueden intentar apostar simultaneamente con el
mismo saldo. Necesitamos prevenir el doble gasto sin sacrificar
consistencia.

## Opciones consideradas

1. **Concurrencia optimista (version columns)**
   - Pros: mejor throughput en baja contension.
   - Contras: requiere logica de reintento explicita. Las race
     conditions se detectan tarde (al hacer commit). Mas complejo
     de testear correctamente.

2. **Bloqueo pesimista con select_for_update() dentro de atomic()**
   - Pros: PostgreSQL bloquea la fila a nivel BD. Cualquier peticion
     concurrente espera o falla limpiamente. Logica de servicio
     simple y lineal. Demostrable con test de threads.
   - Contras: posible cuello de botella si muchos workers leen el
     mismo wallet simultaneamente (no es el caso a esta escala).

## Decision
Adoptamos select_for_update() dentro de transaction.atomic()
en todos los servicios criticos: execute_recharge, execute_bet_lock
y execute_bet_settlement.

El test de concurrencia (10 threads simultaneos con saldo de 100
apostando 20 cada uno) demuestra que nunca se genera doble gasto.

## Consecuencias
- Mas facil: demostrar la invariante "ningun wallet nunca negativo".
- Mas dificil: si en el futuro un servicio lockea wallet y Bet
  simultaneamente, hay que definir orden de adquisicion para evitar
  deadlocks. Orden documentado: siempre wallet antes que Bet.
- Deuda tecnica: a escala mayor considerar optimistic locking
  con reintentos automaticos.

## Fecha y autor
2026-05-23 - Lennart Fustamante