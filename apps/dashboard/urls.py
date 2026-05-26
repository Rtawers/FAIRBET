from django.urls import path  
from apps.dashboard.views import metrics_view, report_csv_view

app_name = "dashboard"

urlpatterns = [
    path("metrics/", metrics_view, name="dashboard-metrics"),
    path("report/csv/", report_csv_view, name="dashboard-report-csv"),
]
