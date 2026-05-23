from decimal import Decimal, ROUND_HALF_UP


def calculate_margin(*odds_list: Decimal) -> Decimal:
    if not odds_list:
        raise ValueError("Se necesita al menos una cuota.")
    total = sum(Decimal("1") / odd for odd in odds_list)
    margin = (total - Decimal("1")) * Decimal("100")
    return margin.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
