from django.urls import path
from frontend import views

app_name = 'frontend'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('wallet/', views.wallet_view, name='wallet'),
    path('eventos/', views.eventos_view, name='eventos'),
    path('eventos/<int:event_id>/', views.evento_detalle_view, name='evento_detalle'),
]