# ADR-0009: Fórmula y contabilidad del cash-out

## Contexto
(El cash-out permite al usuario cerrar una apuesta antes de que termine el
evento, cobrando un monto calculado según las cuotas actuales. Había que definir la
fórmula del monto y cómo registrarlo en la contabilidad de partida doble.)

## Opciones consideradas
1. **Fórmula del reto: stake × odds_original / odds_actual × factor_casa**
   - Pros: (ajusta el pago a la probabilidad actual; el factor_casa da margen a la casa)
   - Contras: (requiere conocer la cuota actual en el momento del cash-out)
2. **Devolver simplemente el stake** (cancelación sin ganancia/pérdida)
   - Pros: (trivial)
   - Contras: (no es un cash-out real; no refleja cómo va la apuesta)

## Decisión
(Elegimos la fórmula del reto. El monto se calcula con calculate_cashout y se registra
con 3 asientos de partida doble que suman cero: PENDING DEBIT stake, WALLET CREDIT cashout,
y CASA ajusta la diferencia —DEBIT si cashout > stake, CREDIT si cashout < stake—.
La Bet pasa a CANCELLED. Todo en Decimal, nunca float.)

## Consecuencias
- Más fácil: (el usuario asegura ganancia/limita pérdida; la contabilidad queda balanceada)
- Más difícil / deuda técnica: (el factor_casa es un parámetro fijo que se pasa a la función;
  en v2 podría venir de configuración o variar por mercado.)

## Fecha y autor
2026-05-24 - Daniel Rodríguez (Rtawers)