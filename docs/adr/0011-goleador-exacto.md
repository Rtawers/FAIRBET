# ADR 0011 — Mercado "goleador exacto" con manejo de empate técnico

## Contexto

La variación única del Bloque 3 incluye un mercado de "goleador exacto":
el usuario apuesta a qué jugador marcará. A diferencia del mercado 1X2,
existe un escenario sin equivalente directo: el empate técnico (0-0),
donde NINGÚN jugador marca. Hay que decidir cómo se liquida ese caso.

## Opciones consideradas

1. **Anular las apuestas si el partido termina 0-0 (VOID):** devolver el
   stake. Descartada: pierde el atractivo del mercado y complica la liquidación.

2. **Selección especial "Sin goleador" (elegida):** el mercado incluye, además
   de los jugadores, una selección "SIN_GOLEADOR" con su propia odds. Si el
   partido termina sin goles, esa selección gana; si marca un jugador, gana
   la suya.

## Decisión

Se adopta la **selección especial "Sin goleador"**. La liquidación
(`liquidar_goleador`) recibe el goleador real (o `None` si fue 0-0) y lo
normaliza: si no hubo goleador, el ganador es la selección SIN_GOLEADOR.
Así un único flujo cubre ambos escenarios sin ramas especiales.

## Consecuencias

- Positivas: el empate técnico es un resultado apostable más, no una excepción.
  La lógica es uniforme (un solo camino para "hubo/no hubo goleador").
- Negativas: el mercado depende de que events incluya la selección
  "Sin goleador" al crearlo; debe coordinarse entre events y betting.

## Fecha y autor

2026-05-26 — Daniel (Rtawers), responsable de betting.