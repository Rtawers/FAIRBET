# frontend/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def wallet_view(request):
    return render(request, 'wallet.html')