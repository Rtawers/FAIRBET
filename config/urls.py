from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/audit/", include("apps.audit.urls")),
    path("api/betting/", include("apps.betting.urls")),
    # Rutas de cada app, ej:
    # path("api/wallet/", include("apps.wallet.urls")),
    
]
