from django.core.exceptions import PermissionDenied, ValidationError
from apps.events.models import EventStatus, MarketStatus
from apps.wallet.models import Bet
from apps.wallet.services import execute_bet_lock


# Estados de evento sobre los que se permite apostar:
# SCHEDULED (pre-partido) y LIVE (in-play).
ESTADOS_APOSTABLES = (EventStatus.SCHEDULED, EventStatus.LIVE)


def place_bet(user, selection, amount):
    # 1. Validación KYC: solo VERIFIED puede apostar
    if user.profile.kyc_status != "VERIFIED":
        raise PermissionDenied("Usuario sin KYC verificado no puede apostar")

    # 2. Validación de evento: solo SCHEDULED (pre-partido) o LIVE (in-play)
    if selection.market.event.status not in ESTADOS_APOSTABLES:
        raise ValidationError("No se puede apostar a este evento (no está programado ni en vivo)")

    # 3. Validación in-play: rechazar si el mercado está suspendido
    #    (Lucrecia suspende el mercado durante eventos críticos vía Celery)
    if selection.market.status == MarketStatus.SUSPENDED:
        raise ValidationError("El mercado está suspendido. No se pueden aceptar apuestas.")

    # 4. Bloquear fondos vía partida doble (wallet -> pending)
    lock_tx = execute_bet_lock(user, amount)

    # 5. Crear la Bet en estado ACCEPTED, asociada a la transacción de bloqueo
    bet = Bet.objects.create(
        user=user,
        amount=amount,
        odds=selection.odds,
        lock_transaction=lock_tx,
    )
    return bet