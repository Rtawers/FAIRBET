from django.core.exceptions import PermissionDenied, ValidationError
from apps.events.models import EventStatus
from apps.wallet.models import Bet
from apps.wallet.services import execute_bet_lock

def place_bet(user, selection, amount):
    # 1. Validación KYC (test 1): solo VERIFIED puede apostar
    if user.profile.kyc_status != "VERIFIED":
        raise PermissionDenied("Usuario sin KYC verificado no puede apostar")

    # 2. Validación de evento (test 2): solo eventos SCHEDULED
    if selection.market.event.status != EventStatus.SCHEDULED:
        raise ValidationError("No se puede apostar a un evento que no está programado")

    # 3. Bloquear fondos vía partida doble (wallet -> pending). Devuelve la Transaction.
    lock_tx = execute_bet_lock(user, amount)

    # 4. Crear la Bet en estado ACCEPTED, asociada a la transacción de bloqueo
    bet = Bet.objects.create(
        user=user,
        amount=amount,
        odds=selection.odds,
        lock_transaction=lock_tx,
    )
    return bet