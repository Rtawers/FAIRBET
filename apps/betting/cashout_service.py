from decimal import Decimal


def calculate_cashout(stake, odds_original, odds_actual, factor_casa):
    # cashout = stake * odds_original / odds_actual * factor_casa
    raw = stake * odds_original / odds_actual * factor_casa
    # Redondeamos a 4 decimales (misma precisión que el dinero del sistema)
    return raw.quantize(Decimal("0.0001"))