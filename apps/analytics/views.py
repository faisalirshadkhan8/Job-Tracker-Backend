from datetime import timedelta

from django.db.models import Avg, Count, F, Q
from django.db.models.functions import TruncMonth, TruncWeek
from django.utils import timezone

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.applications.models import Application
from apps.interviews.models import Interview


class DashboardView(APIView):
    """Main dashboard with key metrics."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        applications = Application.objects.filter(user=user)
        interviews = Interview.objects.filter(application__user=user)

        # Basic counts
        total_apps = applications.count()
        active_apps = applications.exclude(status__in=["rejected", "withdrawn", "ghosted", "accepted"]).count()

        # Status breakdown
        status_counts = dict(applications.values("status").annotate(count=Count("id")).values_list("status", "count"))

        # Upcoming interviews
        upcoming_interviews = interviews.filter(scheduled_at__gte=timezone.now(), status="scheduled").count()

        # Response rate
        apps_with_response = applications.filter(response_date__isnull=False).count()
        response_rate = (apps_with_response / total_apps * 100) if total_apps > 0 else 0

        # Average response time (days)
        apps_with_dates = applications.filter(applied_date__isnull=False, response_date__isnull=False).annotate(
            response_days=F("response_date") - F("applied_date")
        )
        avg_response_days = None
        if apps_with_dates.exists():
            # Calculate average manually since SQLite doesn't support date subtraction well
            total_days = sum((app.response_date - app.applied_date).days for app in apps_with_dates)
            avg_response_days = round(total_days / apps_with_dates.count(), 1)

        return Response(
            {
                "total_applications": total_apps,
                "active_applications": active_apps,
                "offers_received": status_counts.get("offer", 0) + status_counts.get("accepted", 0),
                "interviews_scheduled": upcoming_interviews,
                "response_rate": round(response_rate, 1),
                "avg_response_days": avg_response_days,
                "status_breakdown": status_counts,
            }
        )


class ResponseRateView(APIView):
    """Response rate analytics by source."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Response rate by source
        sources = (
            Application.objects.filter(user=user)
            .values("source")
            .annotate(total=Count("id"), with_response=Count("id", filter=Q(response_date__isnull=False)))
            .order_by("-total")
        )

        source_rates = []
        for source in sources:
            rate = (source["with_response"] / source["total"] * 100) if source["total"] > 0 else 0
            source_rates.append(
                {
                    "source": source["source"],
                    "total": source["total"],
                    "with_response": source["with_response"],
                    "response_rate": round(rate, 1),
                }
            )

        return Response({"by_source": source_rates})


class StatusFunnelView(APIView):
    """Application funnel from applied to offer."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        applications = Application.objects.filter(user=user)
        total = applications.count()

        if total == 0:
            return Response({"funnel": [], "conversion_rates": {}})

        # Define funnel stages
        stages = [
            ("applied", ["applied", "screening", "interviewing", "offer", "accepted"]),
            ("screening", ["screening", "interviewing", "offer", "accepted"]),
            ("interviewing", ["interviewing", "offer", "accepted"]),
            ("offer", ["offer", "accepted"]),
            ("accepted", ["accepted"]),
        ]

        funnel = []
        for stage_name, statuses in stages:
            count = applications.filter(status__in=statuses).count()
            # Also count apps that have passed this stage
            funnel.append({"stage": stage_name, "count": count, "percentage": round(count / total * 100, 1)})

        return Response({"funnel": funnel, "total_applications": total})


class WeeklyActivityView(APIView):
    """Applications per week over time."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Get weeks parameter (default last 12 weeks)
        weeks = int(request.query_params.get("weeks", 12))
        start_date = timezone.now().date() - timedelta(weeks=weeks)

        # Applications per week
        weekly_apps = (
            Application.objects.filter(user=user, applied_date__gte=start_date)
            .annotate(week=TruncWeek("applied_date"))
            .values("week")
            .annotate(count=Count("id"))
            .order_by("week")
        )

        return Response({"weekly_applications": list(weekly_apps), "period_weeks": weeks})


class TopCompaniesView(APIView):
    """Companies with most applications."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        limit = int(request.query_params.get("limit", 10))

        top_companies = (
            Application.objects.filter(user=user)
            .values("company__id", "company__name")
            .annotate(application_count=Count("id"), interview_count=Count("interviews"))
            .order_by("-application_count")[:limit]
        )

        return Response({"top_companies": list(top_companies)})
