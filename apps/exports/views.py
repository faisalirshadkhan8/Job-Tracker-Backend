"""
Export Views - API endpoints for data exports.
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.applications.models import Application
from apps.companies.models import Company
from apps.interviews.models import Interview
from .services import ExportService


class ExportApplicationsView(APIView):
    """Export applications to CSV."""
    
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Export Applications to CSV",
        description="Download all your applications as a CSV file.",
        parameters=[
            OpenApiParameter(
                name='status',
                description='Filter by status',
                required=False,
                type=str
            ),
        ],
        tags=["Exports"]
    )
    def get(self, request):
        applications = Application.objects.filter(
            user=request.user
        ).select_related('company').prefetch_related('notes', 'interviews')
        
        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            applications = applications.filter(status=status_filter)
        
        return ExportService.export_applications_csv(applications)


class ExportCompaniesView(APIView):
    """Export companies to CSV."""
    
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Export Companies to CSV",
        description="Download all your saved companies as a CSV file.",
        tags=["Exports"]
    )
    def get(self, request):
        companies = Company.objects.filter(
            user=request.user
        ).prefetch_related('applications')
        
        return ExportService.export_companies_csv(companies)


class ExportInterviewsView(APIView):
    """Export interviews to CSV."""
    
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Export Interviews to CSV",
        description="Download all your interviews as a CSV file.",
        parameters=[
            OpenApiParameter(
                name='status',
                description='Filter by status (scheduled, completed, cancelled)',
                required=False,
                type=str
            ),
        ],
        tags=["Exports"]
    )
    def get(self, request):
        interviews = Interview.objects.filter(
            application__user=request.user
        ).select_related('application', 'application__company')
        
        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            interviews = interviews.filter(status=status_filter)
        
        return ExportService.export_interviews_csv(interviews)


class ExportFullReportView(APIView):
    """Export complete job search data as ZIP."""
    
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Export Full Report (ZIP)",
        description="Download all your job search data as a ZIP file containing CSVs and a summary.",
        tags=["Exports"]
    )
    def get(self, request):
        return ExportService.export_full_report_csv(request.user)
