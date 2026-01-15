from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import ApplicationViewSet, NoteViewSet, ResumeVersionViewSet

router = DefaultRouter()
router.register("", ApplicationViewSet, basename="application")

# Separate routes for resumes
resume_router = DefaultRouter()
resume_router.register("resumes", ResumeVersionViewSet, basename="resume")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(resume_router.urls)),
]
