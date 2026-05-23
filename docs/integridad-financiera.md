# Integridad financiera

## Como el diseno garantiza la integridad
- Partida doble: cada movimiento = debito + credito, suma global = 0.
- Saldo derivado, nunca almacenado.
- Decimal (18,4), prohibido float.
- Concurrencia: select_for_update + idempotencia.

## Invariantes verificadas con tests
- ...
