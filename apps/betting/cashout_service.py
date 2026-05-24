from decimal import Decimal
from django.db import transaction
from apps.wallet.models import Account, Bet, LedgerEntry, Transaction



def calculate_cashout(stake, odds_original, odds_actual, factor_casa):
    # cashout = stake * odds_original / odds_actual * factor_casa
    raw = stake * odds_original / odds_actual * factor_casa
    # Redondeamos a 4 decimales (misma precisión que el dinero del sistema)
    return raw.quantize(Decimal("0.0001"))

def execute_cashout(bet, odds_actual, factor_casa):
    with transaction.atomic():
        # Bloquear la Bet para evitar cash-out doble concurrente
        bet_locked = Bet.objects.select_for_update().get(pk=bet.pk)

        # Solo se puede cobrar una apuesta ACCEPTED (test 10 validará lo contrario)
        if bet_locked.status != Bet.BetStatus.ACCEPTED:
            raise ValueError(
                f"No se puede hacer cash-out de una apuesta en estado {bet_locked.status}"
            )

        stake = bet_locked.amount
        cashout = calculate_cashout(stake, bet_locked.odds, odds_actual, factor_casa)

        wallet = Account.objects.get(
            user=bet_locked.user, type=Account.AccountType.WALLET
        )
        pending = Account.objects.get(type=Account.AccountType.PENDING)
        casa = Account.objects.get(type=Account.AccountType.CASA)

        tx = Transaction.objects.create(kind=Transaction.Kind.SETTLEMENT)

        # Asiento 1: sale el stake de PENDING (estaba bloqueado)
        LedgerEntry.objects.create(
            transaction=tx, account=pending,
            amount=stake, direction=LedgerEntry.Direction.DEBIT,
        )
        # Asiento 2: entra el cash-out al WALLET del usuario
        LedgerEntry.objects.create(
            transaction=tx, account=wallet,
            amount=cashout, direction=LedgerEntry.Direction.CREDIT,
        )
        # Asiento 3: la CASA ajusta la diferencia para que todo sume cero
        diferencia = (cashout - stake).quantize(Decimal("0.0001"))
        if diferencia > 0:
            # cashout > stake: la casa PONE la diferencia (DEBIT)
            LedgerEntry.objects.create(
                transaction=tx, account=casa,
                amount=diferencia, direction=LedgerEntry.Direction.DEBIT,
            )
        elif diferencia < 0:
            # cashout < stake: la casa SE QUEDA con la diferencia (CREDIT)
            LedgerEntry.objects.create(
                transaction=tx, account=casa,
                amount=-diferencia, direction=LedgerEntry.Direction.CREDIT,
            )
        # si diferencia == 0, no hace falta asiento de casa

        bet_locked.status = Bet.BetStatus.CANCELLED
        bet_locked.save(update_fields=["status"])
        return tx