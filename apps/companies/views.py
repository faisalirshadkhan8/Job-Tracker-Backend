from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import Company
from .serializers import CompanySerializer, CompanyListSerializer


class CompanyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Company CRUD operations.
    Users can only see their own companies.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['size', 'industry']
    search_fields = ['name', 'industry', 'location']
    ordering_fields = ['name', 'created_at', 'glassdoor_rating']
    ordering = ['name']

    def get_queryset(self):
        """Return companies for the current user only."""
        return Company.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Use lightweight serializer for list action."""
        if self.action == 'list':
            return CompanyListSerializer
        return CompanySerializer
