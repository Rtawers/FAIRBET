# ADR 0012 — Rollover fijo de 5x para el bono de bienvenida

## Contexto

El bono de bienvenida acredita fichas virtuales a una cuenta BONUS separada
del usuario al registrarse. Sin restricciones, un usuario podría recibir el
bono y retirarlo de inmediato sin actividad real, lo que vacía el sentido
del bono y abre la puerta a abuso. Se necesita una regla que condicione el
retiro del bono a una actividad mínima de juego.

## Opciones consideradas

1. **Sin rollover:** el bono es retirable de inmediato.
   Descartada: permite abuso (recibir y retirar sin jugar).

2. **Rollover configurable por campo en el modelo:** cada bono define su
   propio múltiplo. Más flexible, pero añade estado a mantener y
   complejidad de coordinación entre apps para un proyecto de este alcance.

3. **Rollover fijo de 5x (elegida):** el usuario debe apostar al menos
   5 veces el monto del bono antes de poder retirar el saldo BONUS.

## Decisión

Se adopta un **rollover fijo de 5x**. El cálculo es **derivado** (no se
almacena un contador): se suma el monto de todas las apuestas del usuario,
excluyendo las canceladas, y se compara con el requerido (bono x 5).

Reglas:
- Las apuestas en estado CANCELLED (deshechas por cash-out) NO cuentan,
  porque el usuario revirtió esa actividad.
- Un usuario sin bono no tiene restricción de retiro.
- Como el bono es de bienvenida (se acredita al registrarse), el usuario no
  tiene apuestas previas; por eso sumar todas sus apuestas equivale a sumar
  las posteriores al bono.

## Consecuencias

- Positivas: regla simple, coherente con la filosofía del proyecto (todo
  derivado, nada almacenado). No requiere campos nuevos ni coordinar estado
  entre wallet y betting. Fácil de auditar y testear.
- Negativas: el múltiplo es fijo; cambiar la política exige modificar la
  constante `ROLLOVER_MULTIPLICADOR`. Aceptable para el alcance actual.
- El cálculo recorre las apuestas del usuario en cada verificación de retiro;
  a gran escala se podría cachear, pero no es necesario en este contexto.

## Fecha y autor

2026-05-26 — Daniel (Rtawers), responsable de betting.