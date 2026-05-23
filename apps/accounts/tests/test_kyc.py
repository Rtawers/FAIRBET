import pytest
from apps.accounts.dni import calcular_digito_verificador

def test_calcular_digito_verificador_retorna_un_solo_caracter():
    dni_ejemplo = "45678912"
    resultado = calcular_digito_verificador(dni_ejemplo)
    
    assert isinstance(resultado, str)
    assert len(resultado) == 1
    assert resultado in "0123456789K"

def test_calcular_digito_verificador_menos_de_ocho_digitos_lanza_value_error():
    dni_corto = "12345"
    with pytest.raises(ValueError):
        calcular_digito_verificador(dni_corto)

def test_calcular_digito_verificador_con_letras_lanza_value_error():
    dni_con_letras = "4567891A"
    with pytest.raises(ValueError, match="El DNI solo debe contener caracteres numericos"):
        calcular_digito_verificador(dni_con_letras)

def test_validar_dni_completo_con_digito_incorrecto_lanza_value_error():
   
    dni_incorrecto = "45678912X" 
    
    with pytest.raises(ValueError, match="El dígito verificador es incorrecto"):
        from apps.accounts.dni import validar_dni
        validar_dni(dni_incorrecto)

@pytest.mark.django_db
def test_user_profile_recien_creado_tiene_estado_pending_verification():
    from django.contrib.auth import get_user_model
    from apps.accounts.models import UserProfile 
    
    User = get_user_model()
    usuario_base = User.objects.create_user(username="maicol_test", password="password123")
    
    perfil = UserProfile.objects.create(
        user=usuario_base,
        dni="45678912"  
    )
    
    assert perfil.kyc_status == "PENDING_VERIFICATION"