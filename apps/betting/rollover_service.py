"""
Servicio de rollover para el bono de bienvenida.

Regla: un usuario que recibió un bono debe apostar al menos 5x el monto
del bono antes de poder retirar el saldo de su cuenta BONUS.

El rollover se calcula de forma derivada (no se almacena un contador):
se suma el monto de todas las apuestas válidas del usuario y se compara
con el requerido. Las apuestas CANCELLED (deshechas por cash-out) NO cuentan.
"""
from decimal import Decimal

from django.db.models import Sum

from apps.wallet.models import Account, Bet, LedgerEntry

# Múltiplo fijo de rollover (documentado en ADR): apostar 5x el bono.
ROLLOVER_MULTIPLICADOR = Decimal("5")


def _obtener_monto_bono(user) -> Decimal:
    """
    Devuelve el saldo acreditado a la cuenta BONUS del usuario.
    Si no tiene cuenta BONUS, devuelve 0.
    """
    bonus = Account.objects.filter(
        user=user, type=Account.AccountType.BONUS
    ).first()
    if bonus is None:
        return Decimal("0.0000")

    total = Decimal("0.0000")
    for entry in bonus.entries.all():
        if entry.direction == LedgerEntry.Direction.CREDIT:
            total += entry.amount
        else:
            total -= entry.amount
    return total


def rollover_cumplido(user) -> bool:
    """
    True si el usuario cumplió el rollover (puede retirar el bono).

    - Sin bono -> no hay restricción (True).
    - Con bono -> debe haber apostado >= 5x el monto del bono.
    - Las apuestas CANCELLED no cuentan hacia el rollover.
    """
    monto_bono = _obtener_monto_bono(user)
    if monto_bono == 0:
        return True

    requerido = monto_bono * ROLLOVER_MULTIPLICADOR

    total_apostado = (
        Bet.objects
        .filter(user=user)
        .exclude(status=Bet.BetStatus.CANCELLED)
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0.0000")
    )

    return total_apostado >= requerido