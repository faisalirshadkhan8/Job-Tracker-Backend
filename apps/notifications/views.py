"""
Notification Views - Manage preferences and view notification history.
"""

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import NotificationLog, NotificationPreference
from .serializers import NotificationLogSerializer, NotificationPreferenceSerializer


class NotificationPreferenceView(APIView):
    """Manage notification preferences."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: NotificationPreferenceSerializer},
        summary="Get Notification Preferences",
        description="Get your notification settings.",
        tags=["Notifications"],
    )
    def get(self, request):
        """Get current notification preferences."""
        prefs, _ = NotificationPreference.objects.get_or_create(user=request.user)
        serializer = NotificationPreferenceSerializer(prefs)
        return Response(serializer.data)

    @extend_schema(
        request=NotificationPreferenceSerializer,
        responses={200: NotificationPreferenceSerializer},
        summary="Update Notification Preferences",
        description="Update your notification settings.",
        tags=["Notifications"],
    )
    def put(self, request):
        """Update notification preferences."""
        prefs, _ = NotificationPreference.objects.get_or_create(user=request.user)
        serializer = NotificationPreferenceSerializer(prefs, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    patch = put  # Allow PATCH as well


@extend_schema_view(
    list=extend_schema(
        summary="List Notification History", description="Get your notification history.", tags=["Notifications"]
    ),
)
class NotificationLogViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """ViewSet for viewing notification history."""

    permission_classes = [IsAuthenticated]
    serializer_class = NotificationLogSerializer

    def get_queryset(self):
        queryset = NotificationLog.objects.filter(user=self.request.user)

        notification_type = self.request.query_params.get("notification_type")
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        return queryset
