from django.core.exceptions import PermissionDenied, ValidationError
from apps.events.models import EventStatus

def place_bet(user, selection):
    # 1. Validación KYC (test 1): solo VERIFIED puede apostar
    if user.profile.kyc_status != "VERIFIED":
        raise PermissionDenied("Usuario sin KYC verificado no puede apostar")

    # 2. Validación de evento (test 2): solo se apuesta a eventos SCHEDULED
    if selection.market.event.status != EventStatus.SCHEDULED:
        raise ValidationError("No se puede apostar a un evento que no está programado")

    # (la creación de la Bet vendrá en el test 3)