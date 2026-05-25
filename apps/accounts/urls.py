from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

@api_view(['POST'])
def dummy_register(request):
    return Response({"detail": "No implementado"}, status=status.HTTP_501_NOT_IMPLEMENTED)

@api_view(['POST'])
def dummy_kyc(request):
    return Response({"detail": "No implementado"}, status=status.HTTP_501_NOT_IMPLEMENTED)

app_name = 'accounts-api'

urlpatterns = [
    path('register/', dummy_register, name='register'),
    path('kyc/', dummy_kyc, name='kyc'),
]