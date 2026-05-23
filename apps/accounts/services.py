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
        
    usuario = User.objects.create_user(username=username, email=email, password=password)
    
    perfil = UserProfile.objects.create(
        user=usuario, 
        dni=dni,
        kyc_status="VERIFIED"
    )
    
    return usuario