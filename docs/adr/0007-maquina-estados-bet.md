# ADR-0007: Máquina de estados de una apuesta (Bet)

## Contexto
(Una apuesta pasa por varios estados a lo largo de su vida —se crea, se
aceptan los fondos, se liquida ganada o perdida, o se cierra anticipadamente—.
Necesitábamos definir qué estados existen y qué transiciones son válidas, para que
una apuesta no pueda, por ejemplo, liquidarse dos veces.)

## Opciones consideradas
1. **Estados explícitos con validación de transición** (PENDING, ACCEPTED, WON, LOST, CANCELLED)
   - Pros: (control claro; se rechazan transiciones inválidas, ej. liquidar una bet ya liquidada)
   - Contras: (más código de validación)
2. **Un simple booleano "liquidada / no liquidada"**
   - Pros: (más simple)
   - Contras: (no distingue ganada de perdida ni de cancelada; insuficiente para auditoría)

## Decisión
(Elegimos los estados explícitos del modelo Bet: PENDING, ACCEPTED, WON, LOST, CANCELLED.
Una apuesta nace en ACCEPTED tras bloquear fondos. La liquidación solo procede desde
ACCEPTED —si no, se lanza error— lo que previene la doble liquidación (test 10).
Para el cash-out usamos CANCELLED, ya que no existe un estado dedicado en el modelo.)

## Consecuencias
- Más fácil: (cada operación valida el estado actual antes de actuar; integridad garantizada)
- Más difícil / deuda técnica: (el cash-out reusa CANCELLED en vez de un estado propio
  CASHED_OUT; en v2 se añadiría ese estado para distinguir cancelación de cash-out.)

## Fecha y autor
2026-05-24 - Daniel Rodríguez (Rtawers)