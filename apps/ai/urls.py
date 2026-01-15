"""
AI URL Configuration.
"""

from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import (
    AITaskViewSet,
    CoverLetterGenerateView,
    GeneratedContentViewSet,
    InterviewQuestionsView,
    JobMatchAnalyzeView,
)

router = DefaultRouter()
router.register(r"history", GeneratedContentViewSet, basename="ai-history")
router.register(r"tasks", AITaskViewSet, basename="ai-tasks")

urlpatterns = [
    # AI Generation Endpoints
    path("cover-letter/generate/", CoverLetterGenerateView.as_view(), name="cover-letter-generate"),
    path("job-match/analyze/", JobMatchAnalyzeView.as_view(), name="job-match-analyze"),
    path("interview-questions/generate/", InterviewQuestionsView.as_view(), name="interview-questions-generate"),
    # History & Tasks Management
    path("", include(router.urls)),
]
