from django.core.exceptions import PermissionDenied


def place_bet(user):
    # Validación KYC: solo usuarios VERIFIED pueden apostar
    if user.profile.kyc_status != "VERIFIED":
        raise PermissionDenied("Usuario sin KYC verificado no puede apostar")
    # (la creación de la apuesta vendrá en el test 3)