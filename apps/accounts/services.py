from datetime import date
from django.contrib.auth import get_user_model
from apps.accounts.models import UserProfile
from apps.accounts.dni import validar_dni

User = get_user_model()

def registrar_usuario_kyc(username, email, password, dni, fecha_nacimiento):
    hoy = date.today()
    edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
    
    if edad < 18:
        raise ValueError("El usuario debe ser mayor de 18 años")
        
    validar_dni(dni)
    
    if UserProfile.objects.filter(dni=dni).exists():
        raise ValueError("El DNI ya se encuentra registrado por otro usuario")
        
    usuario = User.objects.create_user(username=username, email=email, password=password)
    
    # Usamos update_or_create para evitar colisiones con las señales (Signals) de Django
    perfil, created = UserProfile.objects.update_or_create(
        user=usuario,
        defaults={
            "dni": dni,
            "kyc_status": "VERIFIED"
        }
    )
    
    return usuario