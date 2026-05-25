from django.urls import path  # noqa: F401
from apps.audit.views import verify_chain_view

app_name = "audit"

urlpatterns = [
     path("verify/", verify_chain_view, name="verify-chain"),
]
