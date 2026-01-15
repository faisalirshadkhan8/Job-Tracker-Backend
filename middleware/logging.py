"""
Request Logging Middleware.
Logs all API requests with timing, user, and response info.
"""

import json
import logging
import time
import uuid

from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("api.requests")


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all API requests with detailed information.

    Logs include:
    - Request ID (for tracing)
    - HTTP method and path
    - User (if authenticated)
    - Response status code
    - Response time in milliseconds
    - Request body (for POST/PUT/PATCH, sanitized)
    """

    # Paths to exclude from logging (health checks, static files)
    EXCLUDED_PATHS = [
        "/api/v1/analytics/live/",
        "/api/v1/analytics/ready/",
        "/health/",
        "/static/",
        "/media/",
        "/favicon.ico",
    ]

    # Sensitive fields to redact in logs
    SENSITIVE_FIELDS = [
        "password",
        "password1",
        "password2",
        "new_password",
        "old_password",
        "token",
        "access",
        "refresh",
        "secret",
        "api_key",
        "apikey",
        "authorization",
        "credit_card",
    ]

    def process_request(self, request):
        """Start timing and add request ID."""
        request.start_time = time.time()
        request.request_id = str(uuid.uuid4())[:8]
        request._sanitized_body = None
        # Pre-read and sanitize JSON body to avoid RawPostDataException later
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.META.get("CONTENT_TYPE", "")
            if "application/json" in content_type:
                try:
                    if request.body:
                        body = json.loads(request.body.decode("utf-8"))
                        request._sanitized_body = self.sanitize_dict(body)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    request._sanitized_body = None

    def process_response(self, request, response):
        """Log the request after response is generated."""
        # Skip excluded paths
        if any(request.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return response

        # Calculate response time
        start_time = getattr(request, "start_time", time.time())
        duration_ms = (time.time() - start_time) * 1000
        request_id = getattr(request, "request_id", "unknown")

        # Get user info
        user = None
        user_id = None
        if hasattr(request, "user") and request.user.is_authenticated:
            user = request.user.email
            user_id = request.user.id

        # Build log data
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "user": user,
            "user_id": user_id,
            "ip_address": self.get_client_ip(request),
            "user_agent": request.META.get("HTTP_USER_AGENT", "")[:200],
        }

        # Add query params for GET requests
        if request.method == "GET" and request.GET:
            log_data["query_params"] = dict(request.GET)

        # Add request body for mutations (sanitized)
        if request.method in ["POST", "PUT", "PATCH"]:
            if request._sanitized_body:
                log_data["body"] = request._sanitized_body

        # Add response info for errors
        if response.status_code >= 400:
            try:
                log_data["response_body"] = response.content.decode("utf-8")[:500]
            except Exception:
                pass

        # Log at appropriate level
        if response.status_code >= 500:
            logger.error(json.dumps(log_data))
        elif response.status_code >= 400:
            logger.warning(json.dumps(log_data))
        else:
            logger.info(json.dumps(log_data))

        # Add request ID to response header for tracing
        response["X-Request-ID"] = request_id

        return response

    def get_client_ip(self, request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")

    def sanitize_dict(self, data, max_depth=3):
        """Recursively sanitize a dictionary."""
        if max_depth <= 0:
            return "..."

        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                if key.lower() in self.SENSITIVE_FIELDS:
                    sanitized[key] = "[REDACTED]"
                elif isinstance(value, (dict, list)):
                    sanitized[key] = self.sanitize_dict(value, max_depth - 1)
                elif isinstance(value, str) and len(value) > 500:
                    sanitized[key] = value[:500] + "...[truncated]"
                else:
                    sanitized[key] = value
            return sanitized
        elif isinstance(data, list):
            return [self.sanitize_dict(item, max_depth - 1) for item in data[:10]]
        return data
