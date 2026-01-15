"""
Export URL Configuration.
"""

from django.urls import path

from .views import (
    ExportApplicationsView,
    ExportCompaniesView,
    ExportInterviewsView,
    ExportFullReportView,
)

urlpatterns = [
    path('applications/', ExportApplicationsView.as_view(), name='export-applications'),
    path('companies/', ExportCompaniesView.as_view(), name='export-companies'),
    path('interviews/', ExportInterviewsView.as_view(), name='export-interviews'),
    path('full-report/', ExportFullReportView.as_view(), name='export-full-report'),
]
