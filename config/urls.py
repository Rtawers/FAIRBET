from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # API endpoints
    path('api/wallet/', include('apps.wallet.urls', namespace='wallet')),
    path('api/accounts/', include('apps.accounts.urls', namespace='accounts-api')),
    path('api/events/', include('apps.events.urls')),
    path('api/compliance/', include('apps.compliance.urls', namespace='compliance')),
    path('api/betting/', include('apps.betting.urls', namespace='betting')),
    path('api/audit/', include('apps.audit.urls', namespace='audit')),
    path('api/dashboard/', include('apps.dashboard.urls', namespace='dashboard')),
    # Swagger UI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    # Frontend
    path('', include('frontend.urls', namespace='frontend')),
]