from django.contrib import admin
from django.urls import path, include
from apps.accounts import urls as accounts_urls 

urlpatterns = [
    path("admin/", admin.site.urls),
    
    path("api/accounts/", include((accounts_urls.urlpatterns, "accounts-api"), namespace="accounts-api")),
]