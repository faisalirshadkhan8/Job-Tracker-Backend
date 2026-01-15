from django.urls import path

from .views import (
    DashboardView,
    ResponseRateView,
    StatusFunnelView,
    WeeklyActivityView,
    TopCompaniesView
)
from .health import HealthCheckView, ReadinessCheckView, LivenessCheckView

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('response-rate/', ResponseRateView.as_view(), name='response_rate'),
    path('funnel/', StatusFunnelView.as_view(), name='status_funnel'),
    path('weekly/', WeeklyActivityView.as_view(), name='weekly_activity'),
    path('top-companies/', TopCompaniesView.as_view(), name='top_companies'),
    
    # Health checks
    path('health/', HealthCheckView.as_view(), name='health_check'),
    path('ready/', ReadinessCheckView.as_view(), name='readiness_check'),
    path('live/', LivenessCheckView.as_view(), name='liveness_check'),
]
