# ADR-0001: Modelo de Partida Doble para el Wallet

## Contexto
Necesitamos un sistema contable para fichas virtuales que garantice
integridad financiera total: imposible crear o destruir fichas de la
nada, y saldo siempre derivado (nunca almacenado).

## Opciones consideradas

1. **Columna `balance` en Account**
   - Pros: lectura instantanea del saldo.
   - Contras: un UPDATE mal hecho rompe la integridad sin dejar rastro.
     Saldo puede desincronizarse de los movimientos reales.

2. **Partida doble: Account + Transaction + LedgerEntry**
   - Pros: imposible introducir fichas fantasma. Toda transaccion
     debe balancearse a cero. Saldo derivado por SUM(credits) -
     SUM(debits). Auditoria completa de cada movimiento.
   - Contras: lectura de saldo cuesta una agregacion SQL.

## Decision
Adoptamos la **Opcion 2**. La integridad financiera es no negociable.
El costo de la agregacion es despreciable a esta escala.

## Consecuencias
- Mas facil: demostrar invariantes con property-based testing.
- Mas dificil: consultas de saldo requieren agregacion + indices.
- Deuda tecnica: sin cache de saldo, dashboards con muchos usuarios
  pueden necesitar indices compuestos en el futuro.

## Fecha y autor
2026-05-23 - Lennart Fustamante