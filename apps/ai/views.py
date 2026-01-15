"""
AI Views - API endpoints for AI-powered features.
Supports both synchronous and asynchronous (Celery) execution.
"""

import json

from django.conf import settings

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, extend_schema_view

from services.groq_service import GroqService
from services.sanitizer import PromptSanitizer

from .models import AITask, GeneratedContent
from .serializers import (
    AITaskDetailSerializer,
    AITaskSerializer,
    AsyncResponseSerializer,
    CoverLetterInputSerializer,
    CoverLetterOutputSerializer,
    GeneratedContentDetailSerializer,
    GeneratedContentSerializer,
    InterviewQuestionsInputSerializer,
    InterviewQuestionsOutputSerializer,
    JobMatchInputSerializer,
    JobMatchOutputSerializer,
)
from .throttling import AIGenerateThrottle


def should_use_async(data):
    """
    Determine if request should be processed asynchronously.
    Priority: request param > server default setting.
    """
    async_mode = data.get("async_mode")
    if async_mode is not None:
        return async_mode
    return getattr(settings, "AI_ASYNC_ENABLED", False)


class CoverLetterGenerateView(APIView):
    """Generate a personalized cover letter using AI."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [AIGenerateThrottle]

    @extend_schema(
        request=CoverLetterInputSerializer,
        responses={
            200: CoverLetterOutputSerializer,
            202: AsyncResponseSerializer,
        },
        summary="Generate Cover Letter",
        description="Generate a personalized cover letter. Supports async mode via `async_mode` parameter.",
        tags=["AI - Cover Letter"],
    )
    def post(self, request):
        serializer = CoverLetterInputSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        application_id = self._validate_application_id(request.user, data.get("application_id"))
        if data.get("application_id") and application_id is None:
            return Response({"error": "Invalid application_id for this user"}, status=status.HTTP_400_BAD_REQUEST)

        # Get resume text
        resume_text = data.get("resume_text")
        if not resume_text and data.get("resume_version_id"):
            resume_text = self._get_resume_text(request.user, data["resume_version_id"])
            if not resume_text:
                return Response(
                    {"error": "Resume version not found or has no text content"}, status=status.HTTP_400_BAD_REQUEST
                )

        # Sanitize inputs
        job_description = PromptSanitizer.sanitize_job_description(data["job_description"])
        resume_text = PromptSanitizer.sanitize_resume(resume_text)
        company_name = PromptSanitizer.sanitize_company_name(data["company_name"])
        job_title = PromptSanitizer.sanitize_job_title(data["job_title"])
        tone = data.get("tone", "professional")

        # Check if async mode
        if should_use_async(data):
            return self._handle_async(
                request.user, application_id, job_description, resume_text, company_name, job_title, tone
            )

        # Synchronous execution
        return self._handle_sync(
            request.user, application_id, data, job_description, resume_text, company_name, job_title, tone
        )

    def _handle_async(self, user, application_id, job_description, resume_text, company_name, job_title, tone):
        """Queue task for async processing."""
        from .tasks import generate_cover_letter_task

        # Create task record
        task = AITask.objects.create(
            user=user,
            application_id=application_id,
            task_type="cover_letter",
            status="pending",
            input_params={
                "company_name": company_name,
                "job_title": job_title,
                "tone": tone,
            },
        )

        # Queue Celery task
        generate_cover_letter_task.delay(
            task_id=task.id,
            job_description=job_description,
            resume_text=resume_text,
            company_name=company_name,
            job_title=job_title,
            tone=tone,
        )

        return Response(
            {
                "task_id": task.id,
                "status": "pending",
                "message": "Cover letter generation queued. Poll /api/v1/ai/tasks/{task_id}/ for status.",
            },
            status=status.HTTP_202_ACCEPTED,
        )

    def _handle_sync(self, user, application_id, data, job_description, resume_text, company_name, job_title, tone):
        """Process synchronously (original behavior)."""
        try:
            result = GroqService.generate_cover_letter(
                job_description=job_description,
                resume_text=resume_text,
                company_name=company_name,
                job_title=job_title,
                tone=tone,
            )
        except Exception as e:
            return Response({"error": f"AI generation failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        saved_id = None
        if data.get("save_to_history", True):
            saved = GeneratedContent.objects.create(
                user=user,
                application_id=application_id,
                content_type="cover_letter",
                input_job_description=data["job_description"],
                input_resume_text=resume_text,
                input_company_name=data["company_name"],
                input_job_title=data["job_title"],
                input_params={"tone": tone},
                output_content=result["cover_letter"],
                output_metadata=result.get("usage", {}),
                model_used=result["model"],
                tokens_used=result.get("usage", {}).get("total_tokens", 0),
            )
            saved_id = saved.id

        return Response(
            {
                "cover_letter": result["cover_letter"],
                "model": result["model"],
                "tokens_used": result.get("usage", {}).get("total_tokens", 0),
                "saved_id": saved_id,
            }
        )

    def _get_resume_text(self, user, resume_version_id):
        """Fetch resume text from a saved resume version."""
        from apps.applications.models import ResumeVersion

        try:
            resume = ResumeVersion.objects.get(id=resume_version_id, application__user=user)
            return resume.content or ""
        except ResumeVersion.DoesNotExist:
            return None

    def _validate_application_id(self, user, application_id):
        """Return application id if it exists for this user, else None."""
        if not application_id:
            return None
        from apps.applications.models import Application

        return Application.objects.filter(id=application_id, user=user).values_list("id", flat=True).first()


class JobMatchAnalyzeView(APIView):
    """Analyze how well a resume matches a job description."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [AIGenerateThrottle]

    @extend_schema(
        request=JobMatchInputSerializer,
        responses={
            200: JobMatchOutputSerializer,
            202: AsyncResponseSerializer,
        },
        summary="Analyze Job Match",
        description="Get an AI-powered analysis. Supports async mode via `async_mode` parameter.",
        tags=["AI - Job Match"],
    )
    def post(self, request):
        serializer = JobMatchInputSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        application_id = self._validate_application_id(request.user, data.get("application_id"))
        if data.get("application_id") and application_id is None:
            return Response({"error": "Invalid application_id for this user"}, status=status.HTTP_400_BAD_REQUEST)

        # Get resume text
        resume_text = data.get("resume_text")
        if not resume_text and data.get("resume_version_id"):
            resume_text = self._get_resume_text(request.user, data["resume_version_id"])
            if not resume_text:
                return Response(
                    {"error": "Resume version not found or has no text content"}, status=status.HTTP_400_BAD_REQUEST
                )

        # Sanitize inputs
        job_description = PromptSanitizer.sanitize_job_description(data["job_description"])
        resume_text = PromptSanitizer.sanitize_resume(resume_text)

        # Check if async mode
        if should_use_async(data):
            return self._handle_async(request.user, application_id, job_description, resume_text)

        # Synchronous execution
        return self._handle_sync(request.user, application_id, data, job_description, resume_text)

    def _handle_async(self, user, application_id, job_description, resume_text):
        """Queue task for async processing."""
        from .tasks import analyze_job_match_task

        task = AITask.objects.create(
            user=user, application_id=application_id, task_type="job_match", status="pending", input_params={}
        )

        analyze_job_match_task.delay(task_id=task.id, job_description=job_description, resume_text=resume_text)

        return Response(
            {
                "task_id": task.id,
                "status": "pending",
                "message": "Job match analysis queued. Poll /api/v1/ai/tasks/{task_id}/ for status.",
            },
            status=status.HTTP_202_ACCEPTED,
        )

    def _handle_sync(self, user, application_id, data, job_description, resume_text):
        """Process synchronously."""
        try:
            result = GroqService.analyze_job_match(job_description=job_description, resume_text=resume_text)
        except Exception as e:
            return Response({"error": f"AI analysis failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        analysis_content = result["analysis"]
        try:
            analysis_content = json.loads(analysis_content)
        except (json.JSONDecodeError, TypeError):
            pass

        saved_id = None
        if data.get("save_to_history", True):
            saved = GeneratedContent.objects.create(
                user=user,
                application_id=application_id,
                content_type="job_match",
                input_job_description=data["job_description"],
                input_resume_text=resume_text,
                output_content=result["analysis"],
                output_metadata=result.get("usage", {}),
                model_used=result["model"],
                tokens_used=result.get("usage", {}).get("total_tokens", 0),
            )
            saved_id = saved.id

        return Response(
            {
                "analysis": analysis_content,
                "model": result["model"],
                "tokens_used": result.get("usage", {}).get("total_tokens", 0),
                "saved_id": saved_id,
            }
        )

    def _get_resume_text(self, user, resume_version_id):
        from apps.applications.models import ResumeVersion

        try:
            resume = ResumeVersion.objects.get(id=resume_version_id, application__user=user)
            return resume.content or ""
        except ResumeVersion.DoesNotExist:
            return None

    def _validate_application_id(self, user, application_id):
        if not application_id:
            return None
        from apps.applications.models import Application

        return Application.objects.filter(id=application_id, user=user).values_list("id", flat=True).first()


class InterviewQuestionsView(APIView):
    """Generate likely interview questions for a position."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [AIGenerateThrottle]

    @extend_schema(
        request=InterviewQuestionsInputSerializer,
        responses={
            200: InterviewQuestionsOutputSerializer,
            202: AsyncResponseSerializer,
        },
        summary="Generate Interview Questions",
        description="Get AI-generated interview questions. Supports async mode via `async_mode` parameter.",
        tags=["AI - Interview Prep"],
    )
    def post(self, request):
        serializer = InterviewQuestionsInputSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        application_id = self._validate_application_id(request.user, data.get("application_id"))
        if data.get("application_id") and application_id is None:
            return Response({"error": "Invalid application_id for this user"}, status=status.HTTP_400_BAD_REQUEST)

        # Sanitize inputs
        job_description = PromptSanitizer.sanitize_job_description(data["job_description"])
        company_name = PromptSanitizer.sanitize_company_name(data["company_name"])
        job_title = PromptSanitizer.sanitize_job_title(data["job_title"])
        question_count = data.get("question_count", 10)

        # Check if async mode
        if should_use_async(data):
            return self._handle_async(
                request.user, application_id, job_description, company_name, job_title, question_count
            )

        # Synchronous execution
        return self._handle_sync(
            request.user, application_id, data, job_description, company_name, job_title, question_count
        )

    def _handle_async(self, user, application_id, job_description, company_name, job_title, question_count):
        """Queue task for async processing."""
        from .tasks import generate_interview_questions_task

        task = AITask.objects.create(
            user=user,
            application_id=application_id,
            task_type="interview_questions",
            status="pending",
            input_params={
                "company_name": company_name,
                "job_title": job_title,
                "question_count": question_count,
            },
        )

        generate_interview_questions_task.delay(
            task_id=task.id,
            job_description=job_description,
            company_name=company_name,
            job_title=job_title,
            question_count=question_count,
        )

        return Response(
            {
                "task_id": task.id,
                "status": "pending",
                "message": "Interview questions generation queued. Poll /api/v1/ai/tasks/{task_id}/ for status.",
            },
            status=status.HTTP_202_ACCEPTED,
        )

    def _handle_sync(self, user, application_id, data, job_description, company_name, job_title, question_count):
        """Process synchronously."""
        try:
            result = GroqService.generate_interview_questions(
                job_description=job_description,
                company_name=company_name,
                job_title=job_title,
                question_count=question_count,
            )
        except Exception as e:
            return Response({"error": f"AI generation failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        saved_id = None
        if data.get("save_to_history", True):
            saved = GeneratedContent.objects.create(
                user=user,
                application_id=application_id,
                content_type="interview_questions",
                input_job_description=data["job_description"],
                input_company_name=data["company_name"],
                input_job_title=data["job_title"],
                input_params={"question_count": question_count},
                output_content=result["questions"],
                output_metadata=result.get("usage", {}),
                model_used=result["model"],
                tokens_used=result.get("usage", {}).get("total_tokens", 0),
            )
            saved_id = saved.id

        return Response(
            {
                "questions": result["questions"],
                "model": result["model"],
                "tokens_used": result.get("usage", {}).get("total_tokens", 0),
                "saved_id": saved_id,
            }
        )

    def _validate_application_id(self, user, application_id):
        if not application_id:
            return None
        from apps.applications.models import Application

        return Application.objects.filter(id=application_id, user=user).values_list("id", flat=True).first()


# ============== AI Task ViewSet ==============


@extend_schema_view(
    list=extend_schema(
        summary="List AI Tasks", description="Get all your queued/completed AI tasks.", tags=["AI - Tasks"]
    ),
    retrieve=extend_schema(
        summary="Get Task Status & Result",
        description="Get details of a specific AI task including result when completed.",
        tags=["AI - Tasks"],
    ),
    destroy=extend_schema(summary="Delete Task", description="Delete a completed or failed task.", tags=["AI - Tasks"]),
)
class AITaskViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    """ViewSet for managing async AI tasks."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AITask.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return AITaskDetailSerializer
        return AITaskSerializer

    @extend_schema(summary="Get Pending Tasks", description="Get all pending/processing tasks.", tags=["AI - Tasks"])
    @action(detail=False, methods=["get"])
    def pending(self, request):
        """List all pending/processing tasks."""
        pending_tasks = self.get_queryset().filter(status__in=["pending", "processing"])
        serializer = self.get_serializer(pending_tasks, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Cancel Task",
        description="Cancel a pending task (cannot cancel already processing tasks).",
        tags=["AI - Tasks"],
    )
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a pending task."""
        task = self.get_object()

        if task.status != "pending":
            return Response(
                {"error": f"Cannot cancel task with status: {task.status}"}, status=status.HTTP_400_BAD_REQUEST
            )

        task.status = "failed"
        task.error_message = "Cancelled by user"
        task.save(update_fields=["status", "error_message"])

        # Revoke Celery task if it exists
        if task.celery_task_id:
            from config.celery import app

            app.control.revoke(task.celery_task_id, terminate=True)

        return Response({"status": "cancelled"})


# ============== Generated Content History ViewSet ==============


@extend_schema_view(
    list=extend_schema(
        summary="List AI Generation History",
        description="Get all your previously generated AI content.",
        tags=["AI - History"],
    ),
    retrieve=extend_schema(
        summary="Get Generated Content Details",
        description="Get full details of a specific AI-generated content.",
        tags=["AI - History"],
    ),
    destroy=extend_schema(
        summary="Delete Generated Content",
        description="Delete a generated content from your history.",
        tags=["AI - History"],
    ),
)
class GeneratedContentViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    """ViewSet for managing AI-generated content history."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return GeneratedContent.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return GeneratedContentDetailSerializer
        return GeneratedContentSerializer

    @extend_schema(
        summary="Toggle Favorite", description="Mark/unmark a generated content as favorite.", tags=["AI - History"]
    )
    @action(detail=True, methods=["post"])
    def toggle_favorite(self, request, pk=None):
        content = self.get_object()
        content.is_favorite = not content.is_favorite
        content.save(update_fields=["is_favorite"])
        return Response({"is_favorite": content.is_favorite})

    @extend_schema(summary="Rate Content", description="Rate a generated content (1-5 stars).", tags=["AI - History"])
    @action(detail=True, methods=["post"])
    def rate(self, request, pk=None):
        content = self.get_object()
        rating = request.data.get("rating")
        if rating is None or not (1 <= int(rating) <= 5):
            return Response({"error": "Rating must be between 1 and 5"}, status=status.HTTP_400_BAD_REQUEST)
        content.rating = int(rating)
        content.save(update_fields=["rating"])
        return Response({"rating": content.rating})

    @extend_schema(summary="Get Favorites", description="Get all favorited generated content.", tags=["AI - History"])
    @action(detail=False, methods=["get"])
    def favorites(self, request):
        favorites = self.get_queryset().filter(is_favorite=True)
        serializer = self.get_serializer(favorites, many=True)
        return Response(serializer.data)
