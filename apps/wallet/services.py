# apps/wallet/services.py
"""
Servicios del wallet de FairBet Lab.

Politica: toda operacion financiera es atomica (transaction.atomic),
usa select_for_update para prevenir doble gasto, y nunca almacena
el saldo — siempre se deriva de los LedgerEntries.
"""
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q, Sum


def _get_balance(wallet_account) -> Decimal:
    """
    Calcula el saldo derivado de una cuenta WALLET.
    SUM(credits) - SUM(debits). Nunca se almacena.
    """
    from apps.wallet.models import LedgerEntry

    result = LedgerEntry.objects.filter(account=wallet_account).aggregate(
        credits=Sum(
            'amount', filter=Q(direction=LedgerEntry.Direction.CREDIT)
        ),
        debits=Sum(
            'amount', filter=Q(direction=LedgerEntry.Direction.DEBIT)
        ),
    )
    credits = result['credits'] or Decimal('0.0000')
    debits = result['debits'] or Decimal('0.0000')
    return credits - debits


def execute_recharge(user: User, amount: Decimal) -> 'Transaction':
    """
    Recarga fichas virtuales al wallet del usuario.

    Partida doble:
      CASA   DEBIT  amount
      WALLET CREDIT amount
      Suma firmada = 0

    Raises:
      ValueError: si amount <= 0.
    """
    from apps.wallet.models import Account, LedgerEntry, Transaction

    if amount <= Decimal('0'):
        raise ValueError(
            f'El monto de recarga debe ser mayor a cero. Recibido: {amount}'
        )

    with transaction.atomic():
        casa = Account.objects.get(type=Account.AccountType.CASA)
        wallet = Account.objects.get(
            user=user, type=Account.AccountType.WALLET
        )

        tx = Transaction.objects.create(kind=Transaction.Kind.RECHARGE)

        LedgerEntry.objects.create(
            transaction=tx,
            account=casa,
            amount=amount,
            direction=LedgerEntry.Direction.DEBIT,
        )
        LedgerEntry.objects.create(
            transaction=tx,
            account=wallet,
            amount=amount,
            direction=LedgerEntry.Direction.CREDIT,
        )

        return tx


def execute_bet_lock(user: User, amount: Decimal) -> 'Transaction':
    """
    Bloquea fondos del wallet del usuario para una apuesta.

    Partida doble:
      WALLET  DEBIT  amount
      PENDING CREDIT amount
      Suma firmada = 0

    select_for_update previene doble gasto concurrente.

    Raises:
      ValueError: si saldo insuficiente o amount <= 0.
    """
    from apps.wallet.models import Account, LedgerEntry, Transaction

    if amount <= Decimal('0'):
        raise ValueError(
            f'El monto de la apuesta debe ser mayor a cero. Recibido: {amount}'
        )

    with transaction.atomic():
        wallet = Account.objects.select_for_update().get(
            user=user, type=Account.AccountType.WALLET
        )
        pending = Account.objects.get(type=Account.AccountType.PENDING)

        saldo = _get_balance(wallet)
        if saldo < amount:
            raise ValueError(
                f'Saldo insuficiente. Disponible: {saldo}, requerido: {amount}'
            )

        tx = Transaction.objects.create(kind=Transaction.Kind.BET_LOCK)

        LedgerEntry.objects.create(
            transaction=tx,
            account=wallet,
            amount=amount,
            direction=LedgerEntry.Direction.DEBIT,
        )
        LedgerEntry.objects.create(
            transaction=tx,
            account=pending,
            amount=amount,
            direction=LedgerEntry.Direction.CREDIT,
        )

        return tx


def execute_bet_settlement(bet, won: bool) -> 'Transaction':
    """
    Liquida una apuesta resolviendo la partida doble desde PENDING.

    WON (3 entries):
      PENDING DEBIT  stake
      CASA    DEBIT  house_loss  (payout - stake)
      WALLET  CREDIT payout

    LOST (2 entries):
      PENDING DEBIT  stake
      CASA    CREDIT stake

    select_for_update sobre la Bet previene doble liquidacion.

    Raises:
      ValueError: si la apuesta no esta en estado ACCEPTED.
    """
    from apps.wallet.models import Account, Bet, LedgerEntry, Transaction

    with transaction.atomic():
        bet_locked = Bet.objects.select_for_update().get(pk=bet.pk)

        if bet_locked.status != Bet.BetStatus.ACCEPTED:
            raise ValueError(
                f'La apuesta {bet_locked.pk} no esta en estado ACCEPTED. '
                f'Estado actual: {bet_locked.status}'
            )

        wallet = Account.objects.get(
            user=bet_locked.user, type=Account.AccountType.WALLET
        )
        pending = Account.objects.get(type=Account.AccountType.PENDING)
        casa = Account.objects.get(type=Account.AccountType.CASA)

        tx = Transaction.objects.create(kind=Transaction.Kind.SETTLEMENT)
        stake = bet_locked.amount

        if won:
            payout = (stake * bet_locked.odds).quantize(Decimal('0.0001'))
            house_loss = (payout - stake).quantize(Decimal('0.0001'))

            LedgerEntry.objects.create(
                transaction=tx, account=pending,
                amount=stake, direction=LedgerEntry.Direction.DEBIT,
            )
            LedgerEntry.objects.create(
                transaction=tx, account=casa,
                amount=house_loss, direction=LedgerEntry.Direction.DEBIT,
            )
            LedgerEntry.objects.create(
                transaction=tx, account=wallet,
                amount=payout, direction=LedgerEntry.Direction.CREDIT,
            )
            bet_locked.status = Bet.BetStatus.WON
        else:
            LedgerEntry.objects.create(
                transaction=tx, account=pending,
                amount=stake, direction=LedgerEntry.Direction.DEBIT,
            )
            LedgerEntry.objects.create(
                transaction=tx, account=casa,
                amount=stake, direction=LedgerEntry.Direction.CREDIT,
            )
            bet_locked.status = Bet.BetStatus.LOST

        bet_locked.save(update_fields=['status'])
        return tx