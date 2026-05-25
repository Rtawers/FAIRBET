from django.urls import path
from apps.accounts.views import register_user, verify_kyc

app_name = 'accounts-api'

urlpatterns = [
    path('register/', register_user, name='register'),
    path('kyc/', verify_kyc, name='kyc'),
]