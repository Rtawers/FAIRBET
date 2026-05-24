from decimal import Decimal


def calculate_combined_odds(odds_list):
    # La cuota combinada es el producto de todas las cuotas individuales.
    # Arrancamos en 1 (elemento neutro de la multiplicación) y multiplicamos cada una.
    combined = Decimal("1")
    for odd in odds_list:
        combined *= odd
    return combined