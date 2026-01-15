"""
Notification URL Configuration.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import NotificationPreferenceView, NotificationLogViewSet

router = DefaultRouter()
router.register(r'history', NotificationLogViewSet, basename='notification-log')

urlpatterns = [
    path('preferences/', NotificationPreferenceView.as_view(), name='notification-preferences'),
    path('', include(router.urls)),
]
