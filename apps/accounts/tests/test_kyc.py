import pytest
from apps.accounts.dni import calcular_digito_verificador
from hypothesis import given, strategies as st


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

@pytest.mark.django_db
def test_usuario_menor_de_edad_es_rechazado_en_kyc_lanza_value_error():
    from datetime import date
    from apps.accounts.services import registrar_usuario_kyc
    
    fecha_nacimiento_menor = date(2015, 5, 23)
    
    with pytest.raises(ValueError, match="El usuario debe ser mayor de 18 años"):
        registrar_usuario_kyc(
            username="maicol_menor",
            email="menor@fairbet.com",
            password="password123",
            dni="45678912",
            fecha_nacimiento=fecha_nacimiento_menor
        )

@pytest.mark.django_db
def test_usuario_mayor_de_edad_con_dni_valido_pasa_a_estado_verified():
    from datetime import date
    from apps.accounts.services import registrar_usuario_kyc
    
    fecha_nacimiento_valida = date(2000, 1, 1)
    
    usuario = registrar_usuario_kyc(
        username="maicol_valido",
        email="valido@fairbet.com",
        password="password123",
        dni="456789121",
        fecha_nacimiento=fecha_nacimiento_valida
    )
    
    assert usuario.profile.kyc_status == "VERIFIED"

@given(st.text(alphabet="0123456789", min_size=8, max_size=8))
def test_invariante_calcular_digito_verificador_con_hypothesis(dni_aleatorio):
    from apps.accounts.dni import calcular_digito_verificador
    
    resultado = calcular_digito_verificador(dni_aleatorio)
    
    assert len(resultado) == 1
    assert resultado in "0123456789K"

@pytest.mark.django_db
def test_usuario_que_cumple_18_anos_hoy_mismo_es_aceptado_en_kyc():
    from datetime import date, timedelta
    from apps.accounts.services import registrar_usuario_kyc
    
    # Si hoy es 2026-05-23, nació el 2008-05-23 (Cumple 18 justo hoy)
    hoy = date.today()
    fecha_cumple_hoy = date(hoy.year - 18, hoy.month, hoy.day)
    
    usuario = registrar_usuario_kyc(
        username="maicol_cumple_hoy",
        email="hoy@fairbet.com",
        password="password123",
        dni="456789121",  # DNI válido (termina en 1)
        fecha_nacimiento=fecha_cumple_hoy
    )
    
    assert usuario.profile.kyc_status == "VERIFIED"

@pytest.mark.django_db
def test_usuario_que_cumple_18_anos_manana_es_rechazado_lanza_value_error():
    from datetime import date, timedelta
    from apps.accounts.services import registrar_usuario_kyc
    
    hoy = date.today()
    try:
        fecha_cumple_manana = date(hoy.year - 18, hoy.month, hoy.day + 1)
    except ValueError:
        fecha_cumple_manana = hoy - timedelta(days=(18 * 365) - 1)
        
    with pytest.raises(ValueError, match="El usuario debe ser mayor de 18 años"):
        registrar_usuario_kyc(
            username="maicol_cumple_manana",
            email="manana@fairbet.com",
            password="password123",
            dni="456789121",
            fecha_nacimiento=fecha_cumple_manana
        )

@pytest.mark.django_db
def test_intentar_registrar_dos_usuarios_con_el_mismo_dni_lanza_error_de_unicidad():
    from datetime import date
    from apps.accounts.services import registrar_usuario_kyc
    
    fecha_valida = date(2000, 1, 1)
    dni_compartido = "456789121"
    
    registrar_usuario_kyc(
        username="usuario_original",
        email="original@fairbet.com",
        password="password123",
        dni=dni_compartido,
        fecha_nacimiento=fecha_valida
    )
    
     registrar_usuario_kyc(
        username="usuario_impostor",
        email="impostor@fairbet.com",
        password="password123",
        dni=dni_compartido,
        fecha_nacimiento=fecha_valida
    )