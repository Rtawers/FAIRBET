"""
Servicios de métricas para el dashboard de operador.

Calcula indicadores clave de negocio leyendo del ledger contable:
  - GGR (Gross Gaming Revenue): ganancia bruta de la plataforma.
  - Exposure: riesgo vivo de las apuestas activas.
  - Volumen: total apostado y número de apuestas activas.

Ninguna métrica se almacena: todas se derivan del ledger en tiempo real.
"""
from decimal import Decimal

from django.db.models import Sum

from apps.wallet.models import Account, LedgerEntry, Bet, Transaction


def calculate_ggr() -> Decimal:
    """
    GGR (Gross Gaming Revenue) = ganancia bruta de juego de la plataforma.

    Se calcula SOLO sobre las liquidaciones (SETTLEMENT) que afectan a la CASA:
    apuestas perdidas acreditan a la CASA (+stake), apuestas ganadas la
    debitan (-premio). Las recargas NO cuentan: son dinero entrante,
    no ganancia de juego.
    """
    casa = Account.objects.filter(type=Account.AccountType.CASA).first()
    if casa is None:
        return Decimal("0.0000")

    total = Decimal("0.0000")
    entries = casa.entries.filter(
        transaction__kind=Transaction.Kind.SETTLEMENT
    )
    for entry in entries:
        if entry.direction == LedgerEntry.Direction.CREDIT:
            total += entry.amount
        else:
            total -= entry.amount
    return total


def calculate_exposure() -> Decimal:
    """
    Exposure = suma de potential_payout de las apuestas ACCEPTED.

    Representa el riesgo vivo: cuánto tendría que pagar la casa
    si todas las apuestas activas resultaran ganadoras.
    """
    total = Decimal("0.0000")
    for bet in Bet.objects.filter(status=Bet.BetStatus.ACCEPTED):
        total += bet.potential_payout
    return total


def calculate_bet_volume() -> dict:
    """
    Volumen de apuestas activas: monto total apostado y número de apuestas.
    """
    bets = Bet.objects.filter(status=Bet.BetStatus.ACCEPTED)
    monto = bets.aggregate(total=Sum("amount"))["total"] or Decimal("0.0000")
    return {
        "total_apostado": monto,
        "numero_apuestas": bets.count(),
    }