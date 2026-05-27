# frontend/views.py
from django.shortcuts import render


def login_view(request):
    """Página de login — obtiene JWT y lo guarda en localStorage."""
    return render(request, 'login.html')


def wallet_view(request):
    """Página de wallet — saldo, recarga y retiro."""
    return render(request, 'wallet.html')