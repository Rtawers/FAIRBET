from django.urls import path
from frontend import views

app_name = 'frontend'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('wallet/', views.wallet_view, name='wallet'),
    path('eventos/', views.eventos_view, name='eventos'),
    path('eventos/<int:event_id>/', views.evento_detalle_view, name='evento_detalle'),
    path('mis-apuestas/', views.mis_apuestas_view, name='mis_apuestas'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
]