"""
Servicio de liquidación del mercado 'goleador exacto'.

Variación única: a diferencia del 1X2, este mercado contempla el caso
de empate técnico (0-0), donde NINGÚN jugador marca. Para ello existe
una selección especial "SIN_GOLEADOR" que gana cuando no hay goleador.

Reglas de liquidación:
  - Si un jugador marcó: gana su selección, pierden las demás.
  - Si nadie marcó (0-0): gana la selección SIN_GOLEADOR, pierden los jugadores.
"""
from apps.events.models import SelectionResult

# Identificador convencional de la selección "sin goleador" (empate técnico).
SIN_GOLEADOR = "SIN_GOLEADOR"


def liquidar_goleador(selections, goleador_real):
    """
    Determina el resultado (WON/LOST) de cada selección de un mercado
    de goleador exacto, según quién marcó realmente.

    Args:
        selections: iterable de Selection del mercado goleador.
        goleador_real: el 'outcome' del jugador que marcó, o None / "SIN_GOLEADOR"
                       si el partido terminó sin goles (empate técnico).

    Returns:
        dict {selection_id: SelectionResult.WON | SelectionResult.LOST}
    """
    # Normalizamos: si no hubo goleador, el ganador es SIN_GOLEADOR.
    ganador = goleador_real if goleador_real else SIN_GOLEADOR

    resultados = {}
    for sel in selections:
        if sel.outcome == ganador:
            resultados[sel.id] = SelectionResult.WON
        else:
            resultados[sel.id] = SelectionResult.LOST
    return resultados