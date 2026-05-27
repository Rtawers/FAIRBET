# frontend/urls.py
from django.urls import path
from frontend import views

app_name = 'frontend'

urlpatterns = [
    path('wallet/', views.wallet_view, name='wallet'),
]