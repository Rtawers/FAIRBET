from django.urls import path
from apps.accounts.views import register_user, verify_kyc, LoginThrottleView  # <-- Importamos la nueva vista

app_name = 'accounts-api'

urlpatterns = [
    path('register/', register_user, name='register'),
    path('kyc/', verify_kyc, name='kyc'),
    path('login/', LoginThrottleView.as_view(), name='token_obtain_pair'), # <-- Ruta del Login agregada de forma limpia
]