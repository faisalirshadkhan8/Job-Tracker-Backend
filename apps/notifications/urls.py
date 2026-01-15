"""
Notification URL Configuration.
"""

from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import NotificationLogViewSet, NotificationPreferenceView

router = DefaultRouter()
router.register(r"history", NotificationLogViewSet, basename="notification-log")

urlpatterns = [
    path("preferences/", NotificationPreferenceView.as_view(), name="notification-preferences"),
    path("", include(router.urls)),
]
