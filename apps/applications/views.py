from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend

from .models import Application, Note, ResumeVersion
from .serializers import (
    ApplicationDetailSerializer,
    ApplicationListSerializer,
    ApplicationSerializer,
    ApplicationStatusUpdateSerializer,
    NoteSerializer,
    ResumeUploadSerializer,
    ResumeVersionSerializer,
)


class ApplicationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Application CRUD operations.
    Users can only see their own applications.
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "priority", "work_type", "source", "company"]
    search_fields = ["job_title", "company__name", "location"]
    ordering_fields = ["applied_date", "updated_at", "created_at", "priority", "status"]
    ordering = ["-updated_at"]

    def get_queryset(self):
        """Return applications for the current user only."""
        return Application.objects.filter(user=self.request.user).select_related("company")

    def get_serializer_class(self):
        """Use appropriate serializer based on action."""
        if self.action == "list":
            return ApplicationListSerializer
        if self.action == "retrieve":
            return ApplicationDetailSerializer
        if self.action == "update_status":
            return ApplicationStatusUpdateSerializer
        return ApplicationSerializer

    @action(detail=True, methods=["patch"], url_path="status")
    def update_status(self, request, pk=None):
        """Quick endpoint for status updates."""
        application = self.get_object()
        serializer = ApplicationStatusUpdateSerializer(application, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(ApplicationSerializer(application).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get", "post"])
    def notes(self, request, pk=None):
        """Get or create notes for an application."""
        application = self.get_object()

        if request.method == "GET":
            notes = application.notes.all()
            serializer = NoteSerializer(notes, many=True)
            return Response(serializer.data)

        elif request.method == "POST":
            serializer = NoteSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(application=application)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NoteViewSet(viewsets.ModelViewSet):
    """ViewSet for Note CRUD operations."""

    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return notes for applications owned by current user."""
        return Note.objects.filter(application__user=self.request.user)


class ResumeVersionViewSet(viewsets.ModelViewSet):
    """ViewSet for Resume Version management with file upload."""

    serializer_class = ResumeVersionSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        """Return resumes for the current user only."""
        return ResumeVersion.objects.filter(user=self.request.user)

    @action(detail=False, methods=["post"], url_path="upload")
    def upload(self, request):
        """
        Upload a new resume file.

        Accepts multipart/form-data with:
        - file: The resume file (PDF or Word)
        - version_name: Name for this version (e.g., "Backend Focus")
        - is_default: (optional) Set as default resume
        """
        serializer = ResumeUploadSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        file = serializer.validated_data["file"]
        version_name = serializer.validated_data["version_name"]
        is_default = serializer.validated_data.get("is_default", False)

        try:
            from services.cloudinary_service import CloudinaryService

            # Upload to Cloudinary
            result = CloudinaryService.upload_resume(file, request.user.id, version_name)

            # Create database record
            resume = ResumeVersion.objects.create(
                user=request.user,
                version_name=version_name,
                file_url=result["url"],
                file_name=result["filename"],
                cloudinary_public_id=result["public_id"],
                file_size=result["size"],
                is_default=is_default,
            )

            return Response(ResumeVersionSerializer(resume).data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["post"], url_path="set-default")
    def set_default(self, request, pk=None):
        """Set a resume version as default."""
        resume = self.get_object()
        resume.is_default = True
        resume.save()
        return Response(ResumeVersionSerializer(resume).data)

    def destroy(self, request, *args, **kwargs):
        """Delete resume and its file from Cloudinary."""
        resume = self.get_object()

        # Delete from Cloudinary
        if resume.cloudinary_public_id:
            try:
                from services.cloudinary_service import CloudinaryService

                CloudinaryService.delete_file(resume.cloudinary_public_id)
            except Exception:
                pass  # Continue even if Cloudinary delete fails

        return super().destroy(request, *args, **kwargs)
