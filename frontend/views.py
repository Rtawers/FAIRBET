from django.shortcuts import render


def login_view(request):
    return render(request, 'login.html')


def wallet_view(request):
    return render(request, 'wallet.html')


def eventos_view(request):
    return render(request, 'eventos.html')


def evento_detalle_view(request, event_id):
    return render(request, 'evento_detalle.html', {'event_id': event_id})


def mis_apuestas_view(request):
    return render(request, 'mis_apuestas.html')


def perfil_view(request):
    return render(request, 'perfil.html')