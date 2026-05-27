from django.contrib import admin
from apps.wallet.models import Account, Transaction, LedgerEntry, Bet

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'type', 'currency']
    list_filter = ['type', 'currency']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'kind', 'created_at', 'idempotency_key']
    list_filter = ['kind']

@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ['id', 'account', 'amount', 'direction', 'transaction']
    list_filter = ['direction']

@admin.register(Bet)
class BetAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'amount', 'odds', 'status', 'created_at']
    list_filter = ['status']