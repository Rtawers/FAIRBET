from django.contrib import admin
from apps.compliance.models import SelfExclusion, DepositLimit

@admin.register(SelfExclusion)
class SelfExclusionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user']

@admin.register(DepositLimit)
class DepositLimitAdmin(admin.ModelAdmin):
    list_display = ['id', 'user']