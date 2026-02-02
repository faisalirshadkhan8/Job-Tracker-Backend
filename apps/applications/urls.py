from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import ApplicationViewSet, ResumeVersionViewSet

router = DefaultRouter()
# Register resumes FIRST (more specific route)
router.register("resumes", ResumeVersionViewSet, basename="resume")
# Register applications with empty prefix LAST (catch-all)
router.register("", ApplicationViewSet, basename="application")

urlpatterns = [
    path("", include(router.urls)),
]
