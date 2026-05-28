# apps/wallet/urls.py
from django.urls import path
from apps.wallet.views import BalanceView, RechargeView, WithdrawView, TransactionHistoryView

app_name = 'wallet'

urlpatterns = [
    path('balance/', BalanceView.as_view(), name='balance'),
    path('recharge/', RechargeView.as_view(), name='recharge'),
    path('withdraw/', WithdrawView.as_view(), name='withdraw'),
    path('transactions/', TransactionHistoryView.as_view(), name='transactions'),
]