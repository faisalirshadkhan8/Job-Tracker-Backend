"""
Custom throttling classes for rate limiting.
"""

from rest_framework.throttling import UserRateThrottle


class AIGenerateThrottle(UserRateThrottle):
    """
    Rate limit for AI generation endpoints.
    Prevents abuse of expensive AI API calls.

    Default: 20 requests per hour (configurable in settings)
    """

    scope = "ai_generate"

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {"scope": self.scope, "ident": ident}


class AIHistoryThrottle(UserRateThrottle):
    """
    Rate limit for AI history endpoints (less restrictive).
    """

    scope = "ai_history"
