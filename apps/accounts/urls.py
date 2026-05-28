from django.urls import path
from apps.accounts.views import register_user, verify_kyc, LoginThrottleView, me_view

app_name = 'accounts-api'

urlpatterns = [
    path('register/', register_user, name='register'),
    path('kyc/', verify_kyc, name='kyc'),
    path('login/', LoginThrottleView.as_view(), name='token_obtain_pair'),
    path('me/', me_view, name='me'),
]