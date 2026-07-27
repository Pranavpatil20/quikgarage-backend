from django.urls import path

from .views import OwnerDashboardMetricsView

urlpatterns = [
    path('owner/metrics/', OwnerDashboardMetricsView.as_view(), name='owner-dashboard-metrics'),
]
