from django.utils import timezone

from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend

from .models import Interview
from .serializers import InterviewListSerializer, InterviewOutcomeSerializer, InterviewSerializer


class InterviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Interview CRUD operations.
    Users can only see interviews for their own applications.
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "outcome", "interview_type", "application"]
    search_fields = ["application__job_title", "application__company__name", "interviewer_names"]
    ordering_fields = ["scheduled_at", "created_at", "round_number"]
    ordering = ["scheduled_at"]

    def get_queryset(self):
        """Return interviews for applications owned by current user."""
        return Interview.objects.filter(application__user=self.request.user).select_related("application__company")

    def get_serializer_class(self):
        """Use appropriate serializer based on action."""
        if self.action == "list":
            return InterviewListSerializer
        if self.action == "update_outcome":
            return InterviewOutcomeSerializer
        return InterviewSerializer

    @action(detail=False, methods=["get"])
    def upcoming(self, request):
        """Get all upcoming interviews."""
        upcoming = (
            self.get_queryset().filter(scheduled_at__gte=timezone.now(), status="scheduled").order_by("scheduled_at")
        )
        serializer = InterviewListSerializer(upcoming, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def today(self, request):
        """Get today's interviews."""
        today = timezone.now().date()
        interviews = self.get_queryset().filter(scheduled_at__date=today).order_by("scheduled_at")
        serializer = InterviewListSerializer(interviews, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["patch"], url_path="outcome")
    def update_outcome(self, request, pk=None):
        """Update interview outcome after completion."""
        interview = self.get_object()
        serializer = InterviewOutcomeSerializer(interview, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(InterviewSerializer(interview).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
