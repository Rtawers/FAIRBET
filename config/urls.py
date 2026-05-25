from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/wallet/', include('apps.wallet.urls', namespace='wallet')),
]