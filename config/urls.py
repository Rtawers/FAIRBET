from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    # Rutas de cada app, ej:
    # path("api/wallet/", include("apps.wallet.urls")),
    # path("api/betting/", include("apps.betting.urls")),
    path("api/compliance/", include("apps.compliance.urls")),

]
