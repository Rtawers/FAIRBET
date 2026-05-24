from decimal import Decimal
from apps.events.models import SelectionResult
from django.core.exceptions import ValidationError


def calculate_combined_odds(odds_list):
    # La cuota combinada es el producto de todas las cuotas individuales.
    # Arrancamos en 1 (elemento neutro de la multiplicación) y multiplicamos cada una.
    combined = Decimal("1")
    for odd in odds_list:
        combined *= odd
    return combined

def is_combined_won(results):
    # La combinada gana SOLO si todas las selecciones ganaron.
    # all() devuelve True únicamente si cada elemento cumple la condición.
    return all(r == SelectionResult.WON for r in results)

def validate_combined_selections(selections):
    # Cada selección pertenece a un evento (selection.market.event).
    # Si hay eventos repetidos, hay selecciones mutuamente excluyentes -> rechazar.
    event_ids = [s.market.event_id for s in selections]
    if len(event_ids) != len(set(event_ids)):
        raise ValidationError("No se pueden combinar selecciones del mismo evento")