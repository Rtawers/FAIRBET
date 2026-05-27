# ADR-0010: Mercado "Goleador Exacto" con manejo de empate técnico

## Contexto
El reto asigna a nuestro equipo la variación obligatoria del mercado
"goleador exacto". A diferencia del mercado 1X2, este mercado tiene
una regla especial: si el partido termina 0-0 (nadie marca), ningún
jugador gana. Para cubrir este caso, el mercado debe incluir siempre
una selección especial "Sin Goleador" que gana cuando nadie anota.
La decisión principal fue cómo modelar esta selección especial y
cómo integrarla con el sistema de liquidación de Daniel en betting.

## Opciones consideradas

1. **Manejar el empate técnico en la capa de liquidación (betting)**
   — Daniel detecta el 0-0 y anula todas las selecciones sin ganador.
   - Pro: no requiere cambios en events.
   - Contra: la lógica de negocio queda en betting, que no conoce
     las reglas del mercado. Viola el principio de que cada app
     conoce su propio dominio.

2. **Campo booleano `is_no_scorer` en Selection** — marcar una
   selección especial con un flag.
   - Pro: explícito en el modelo.
   - Contra: agrega complejidad al modelo para un solo caso.
     El sistema de liquidación ya funciona con `outcome` como
     identificador único.

3. **Selección especial con outcome="SIN_GOLEADOR" dentro del mercado** ✓
   — incluir siempre una selección `SIN_GOLEADOR` con sus propias odds
   usando el modelo `Selection` existente sin modificarlo.
   - Pro: reutiliza el modelo existente sin cambios. La liquidación
     funciona igual que cualquier otro mercado — simplemente gana
     la selección con `outcome="SIN_GOLEADOR"` si nadie marcó.
     Daniel no necesita lógica especial en betting.
   - Contra: el nombre "SIN_GOLEADOR" es un contrato implícito entre
     events y betting. Debe documentarse para futuros desarrolladores.

## Decision
**Selección especial con outcome="SIN_GOLEADOR".**

La razón principal es que no requiere modificar el modelo `Selection`
ni la lógica de liquidación de betting. El sistema ya sabe liquidar
por outcome — solo necesita saber que `outcome="SIN_GOLEADOR"` gana
cuando el resultado es 0-0. Esto mantiene la separación de dominios:
events define el mercado, betting liquida según el outcome ganador.

El método `create_goleador_exacto_market()` en `Market` garantiza
atómicamente que `SIN_GOLEADOR` siempre esté presente — si falla
cualquier selección, la transacción revierte completa.

## Consecuencias
Más fácil:
- Daniel conecta su `place_bet` y liquidación sin cambios.
- El test verifica que `SIN_GOLEADOR` siempre existe en el mercado.
- La atomicidad garantiza consistencia aunque fallen odds inválidas.

Más difícil:
- `outcome="SIN_GOLEADOR"` es un string hardcodeado que actúa
  como contrato entre events y betting.
- No hay validación de que los jugadores correspondan al partido.

Deuda técnica:
- En una v2 se podría extraer `SIN_GOLEADOR` como constante
  compartida entre apps.
- No implementamos odds dinámicas para el goleador exacto.

## Fecha y autor
2026-05-26 - LuviMontes-P