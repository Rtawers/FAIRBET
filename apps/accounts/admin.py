from django.contrib import admin
from apps.accounts.models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'dni', 'kyc_status']
    list_filter = ['kyc_status']
    search_fields = ['user__username', 'dni']
    list_editable = ['kyc_status']