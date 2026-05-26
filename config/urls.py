from django.contrib import admin
from django.urls import path, include
from apps.accounts import urls as accounts_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/compliance/", include("apps.compliance.urls")),

    # Cuentas (Registro, KYC y ahora LOGIN)
    path(
        "api/accounts/",
        include((accounts_urls.urlpatterns, "accounts-api"), namespace="accounts-api")
    ),

    # Demás módulos del sistema
    path('api/wallet/', include('apps.wallet.urls', namespace='wallet')),
    path("api/audit/", include("apps.audit.urls")),
    path("api/betting/", include("apps.betting.urls")),
    path("api/dashboard/", include("apps.dashboard.urls")),
    
]