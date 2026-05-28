from django.core.exceptions import PermissionDenied, ValidationError
from apps.events.models import EventStatus, MarketStatus
from apps.wallet.models import Bet
from apps.wallet.services import execute_bet_lock
from apps.compliance.services import is_user_self_excluded

ESTADOS_APOSTABLES = (EventStatus.SCHEDULED, EventStatus.LIVE)

def place_bet(user, selection, amount):
    # 1. Validación KYC
    if user.profile.kyc_status != "VERIFIED":
        raise PermissionDenied("Usuario sin KYC verificado no puede apostar")

    # 2. Validación autoexclusión
    if is_user_self_excluded(user):
        raise PermissionDenied("Usuario autoexcluido no puede realizar apuestas")

    # 3. Validación de evento
    if selection.market.event.status not in ESTADOS_APOSTABLES:
        raise ValidationError("No se puede apostar a este evento (no está programado ni en vivo)")

    # 4. Validación in-play
    if selection.market.status == MarketStatus.SUSPENDED:
        raise ValidationError("El mercado está suspendido. No se pueden aceptar apuestas.")

    # 5. Bloquear fondos
    lock_tx = execute_bet_lock(user, amount)

    # 6. Crear la Bet
    bet = Bet.objects.create(
        user=user,
        amount=amount,
        odds=selection.odds,
        lock_transaction=lock_tx,
    )
    return bet