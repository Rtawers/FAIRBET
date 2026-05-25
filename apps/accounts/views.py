from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

def calcular_modulo11_reniec(dni_str):
    """
    Algoritmo oficial Módulo 11 para DNI Peruano (Reniec).
    """
    if not dni_str or len(dni_str) != 8 or not dni_str.isdigit():
        return None
        
    factores = [3, 2, 7, 6, 5, 4, 3, 2]
    suma = sum(int(dni_str[i]) * factores[i] for i in range(8))
    
    residuo = suma % 11
    resultado = 11 - residuo
    
    if resultado == 11:
        return "0"
    elif resultado == 10:
        return "1"
    else:
        return str(resultado)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({"error": "Datos incompletos"}, status=status.HTTP_400_BAD_REQUEST)
        
    if User.objects.filter(username=username).exists():
        return Response({"error": "El usuario ya existe"}, status=status.HTTP_400_BAD_REQUEST)
        
    user = User.objects.create_user(username=username, email=email, password=password)
    
    return Response({
        "message": "Usuario creado con éxito",
        "kyc_status": user.profile.kyc_status  
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_kyc(request):
    dni_number = request.data.get('dni_number')
    verification_digit = request.data.get('verification_digit')
    
    if not dni_number or not verification_digit:
        return Response({"error": "Parámetros incompletos de DNI"}, status=status.HTTP_400_BAD_REQUEST)
        
    digito_calculado = calcular_modulo11_reniec(str(dni_number))
    
    if str(verification_digit) == digito_calculado:
        profile = request.user.profile
        profile.kyc_status = "VERIFIED"
        profile.save()
        
        return Response({
            "status": "VERIFIED",
            "kyc_status": profile.kyc_status  
        }, status=status.HTTP_200_OK)
        
    return Response({"error": "DNI inválido por algoritmo Módulo 11"}, status=status.HTTP_400_BAD_REQUEST)