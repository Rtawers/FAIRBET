from django.urls import path
from .views import SelfExclusionAPIView, DepositLimitAPIView

app_name = 'compliance'

urlpatterns = [
    path('self-exclusion/', SelfExclusionAPIView.as_view(), name='self_exclusion'),
    path('deposit-limit/', DepositLimitAPIView.as_view(), name='deposit_limit'),
]