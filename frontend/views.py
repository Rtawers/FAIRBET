# frontend/views.py
from django.shortcuts import render


def login_view(request):
    return render(request, 'login.html')


def wallet_view(request):
    return render(request, 'wallet.html')


def eventos_view(request):
    return render(request, 'eventos.html')