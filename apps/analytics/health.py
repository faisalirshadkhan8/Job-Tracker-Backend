"""
Health Check Views - For monitoring and load balancer checks.
"""

from django.core.cache import cache
from django.db import connection

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema


class HealthCheckView(APIView):
    """
    Health check endpoint for monitoring.
    Returns status of database and cache connections.
    """

    permission_classes = [AllowAny]
    authentication_classes = []  # No auth required

    @extend_schema(
        summary="Health Check",
        description="Check if the API and its dependencies are healthy.",
        tags=["System"],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "database": {"type": "string"},
                    "cache": {"type": "string"},
                },
            }
        },
    )
    def get(self, request):
        health = {
            "status": "healthy",
            "database": "unknown",
            "cache": "unknown",
        }

        # Check database
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health["database"] = "connected"
        except Exception as e:
            health["database"] = f"error: {str(e)}"
            health["status"] = "unhealthy"

        # Check cache (Redis)
        try:
            cache.set("health_check", "ok", 10)
            if cache.get("health_check") == "ok":
                health["cache"] = "connected"
            else:
                health["cache"] = "error: read failed"
                health["status"] = "degraded"
        except Exception as e:
            health["cache"] = f"unavailable: {str(e)}"
            # Cache failure is degraded, not unhealthy
            if health["status"] == "healthy":
                health["status"] = "degraded"

        status_code = 200 if health["status"] != "unhealthy" else 503
        return Response(health, status=status_code)


class ReadinessCheckView(APIView):
    """
    Readiness check - is the app ready to receive traffic?
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        summary="Readiness Check", description="Check if the API is ready to receive traffic.", tags=["System"]
    )
    def get(self, request):
        # Check database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return Response({"ready": True})
        except Exception:
            return Response({"ready": False}, status=503)


class LivenessCheckView(APIView):
    """
    Liveness check - is the app alive?
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(summary="Liveness Check", description="Check if the API process is alive.", tags=["System"])
    def get(self, request):
        return Response({"alive": True})
