from django.urls import path
from .views import SelfExclusionAPIView

app_name = 'compliance'

urlpatterns = [
    path('self-exclusion/', SelfExclusionAPIView.as_view(), name='self_exclusion'),
]