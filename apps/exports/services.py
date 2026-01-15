"""
Export Service - Generate CSV and PDF exports.
"""

import csv
import io
from datetime import datetime

from django.http import HttpResponse


class ExportService:
    """Service for exporting user data to various formats."""

    @staticmethod
    def export_applications_csv(applications):
        """
        Export applications to CSV format.

        Args:
            applications: QuerySet of Application objects

        Returns:
            HttpResponse with CSV content
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Header row
        headers = [
            "Company",
            "Job Title",
            "Status",
            "Priority",
            "Work Type",
            "Location",
            "Source",
            "Applied Date",
            "Response Date",
            "Salary Min",
            "Salary Max",
            "Job URL",
            "Notes Count",
            "Interviews Count",
            "Days Since Applied",
            "Created At",
        ]
        writer.writerow(headers)

        # Data rows
        for app in applications:
            writer.writerow(
                [
                    app.company.name,
                    app.job_title,
                    app.get_status_display(),
                    app.get_priority_display(),
                    app.get_work_type_display() if app.work_type else "",
                    app.location,
                    app.get_source_display(),
                    app.applied_date.strftime("%Y-%m-%d") if app.applied_date else "",
                    app.response_date.strftime("%Y-%m-%d") if app.response_date else "",
                    app.salary_min or "",
                    app.salary_max or "",
                    app.job_url,
                    app.notes.count(),
                    app.interviews.count(),
                    app.days_since_applied or "",
                    app.created_at.strftime("%Y-%m-%d %H:%M"),
                ]
            )

        # Create response
        output.seek(0)
        response = HttpResponse(output.read(), content_type="text/csv")
        filename = f"applications_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response

    @staticmethod
    def export_companies_csv(companies):
        """Export companies to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)

        headers = [
            "Company Name",
            "Website",
            "Industry",
            "Size",
            "Location",
            "Applications Count",
            "Notes",
            "Created At",
        ]
        writer.writerow(headers)

        for company in companies:
            writer.writerow(
                [
                    company.name,
                    company.website,
                    company.industry,
                    company.size,
                    company.location,
                    company.applications.count(),
                    company.notes,
                    company.created_at.strftime("%Y-%m-%d %H:%M"),
                ]
            )

        output.seek(0)
        response = HttpResponse(output.read(), content_type="text/csv")
        filename = f"companies_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response

    @staticmethod
    def export_interviews_csv(interviews):
        """Export interviews to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)

        headers = [
            "Company",
            "Job Title",
            "Round",
            "Type",
            "Status",
            "Outcome",
            "Scheduled At",
            "Duration (min)",
            "Meeting Link",
            "Location",
            "Interviewer Names",
            "Interviewer Titles",
            "Created At",
        ]
        writer.writerow(headers)

        for interview in interviews:
            writer.writerow(
                [
                    interview.application.company.name,
                    interview.application.job_title,
                    interview.round_number,
                    interview.get_interview_type_display(),
                    interview.get_status_display(),
                    interview.get_outcome_display(),
                    interview.scheduled_at.strftime("%Y-%m-%d %H:%M"),
                    interview.duration_minutes,
                    interview.meeting_link,
                    interview.meeting_location,
                    interview.interviewer_names,
                    interview.interviewer_titles,
                    interview.created_at.strftime("%Y-%m-%d %H:%M"),
                ]
            )

        output.seek(0)
        response = HttpResponse(output.read(), content_type="text/csv")
        filename = f"interviews_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response

    @staticmethod
    def export_full_report_csv(user):
        """
        Export complete job search data for a user.
        Returns a ZIP file with all CSVs.
        """
        import zipfile

        from apps.applications.models import Application
        from apps.companies.models import Company
        from apps.interviews.models import Interview

        # Create in-memory ZIP
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Applications CSV
            apps = Application.objects.filter(user=user).select_related("company")
            apps_csv = ExportService._generate_applications_csv_content(apps)
            zip_file.writestr("applications.csv", apps_csv)

            # Companies CSV
            companies = Company.objects.filter(user=user)
            companies_csv = ExportService._generate_companies_csv_content(companies)
            zip_file.writestr("companies.csv", companies_csv)

            # Interviews CSV
            interviews = Interview.objects.filter(application__user=user).select_related(
                "application", "application__company"
            )
            interviews_csv = ExportService._generate_interviews_csv_content(interviews)
            zip_file.writestr("interviews.csv", interviews_csv)

            # Summary text file
            summary = ExportService._generate_summary(user, apps, companies, interviews)
            zip_file.writestr("summary.txt", summary)

        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer.read(), content_type="application/zip")
        filename = f"job_search_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response

    @staticmethod
    def _generate_applications_csv_content(applications):
        """Generate CSV content as string."""
        output = io.StringIO()
        writer = csv.writer(output)

        headers = ["Company", "Job Title", "Status", "Priority", "Applied Date", "Source", "Location"]
        writer.writerow(headers)

        for app in applications:
            writer.writerow(
                [
                    app.company.name,
                    app.job_title,
                    app.get_status_display(),
                    app.get_priority_display(),
                    app.applied_date.strftime("%Y-%m-%d") if app.applied_date else "",
                    app.get_source_display(),
                    app.location,
                ]
            )

        return output.getvalue()

    @staticmethod
    def _generate_companies_csv_content(companies):
        """Generate CSV content as string."""
        output = io.StringIO()
        writer = csv.writer(output)

        headers = ["Company Name", "Website", "Industry", "Size", "Location"]
        writer.writerow(headers)

        for company in companies:
            writer.writerow(
                [
                    company.name,
                    company.website,
                    company.industry,
                    company.size,
                    company.location,
                ]
            )

        return output.getvalue()

    @staticmethod
    def _generate_interviews_csv_content(interviews):
        """Generate CSV content as string."""
        output = io.StringIO()
        writer = csv.writer(output)

        headers = ["Company", "Position", "Type", "Scheduled", "Status", "Outcome"]
        writer.writerow(headers)

        for interview in interviews:
            writer.writerow(
                [
                    interview.application.company.name,
                    interview.application.job_title,
                    interview.get_interview_type_display(),
                    interview.scheduled_at.strftime("%Y-%m-%d %H:%M"),
                    interview.get_status_display(),
                    interview.get_outcome_display(),
                ]
            )

        return output.getvalue()

    @staticmethod
    def _generate_summary(user, applications, companies, interviews):
        """Generate summary text file."""
        from collections import Counter

        from django.utils import timezone

        now = timezone.now()

        # Calculate stats
        status_counts = Counter(app.status for app in applications)
        source_counts = Counter(app.source for app in applications)

        summary = f"""
JOB SEARCH EXPORT SUMMARY
=========================
Generated: {now.strftime('%Y-%m-%d %H:%M:%S')}
User: {user.email}

OVERVIEW
--------
Total Applications: {applications.count()}
Total Companies: {companies.count()}
Total Interviews: {interviews.count()}

APPLICATION STATUS BREAKDOWN
----------------------------
"""
        for status, count in sorted(status_counts.items()):
            display = dict(applications.model.STATUS_CHOICES).get(status, status)
            summary += f"  {display}: {count}\n"

        summary += """
APPLICATION SOURCES
-------------------
"""
        for source, count in sorted(source_counts.items(), key=lambda x: -x[1]):
            display = dict(applications.model.SOURCE_CHOICES).get(source, source)
            summary += f"  {display}: {count}\n"

        summary += """
---
Exported from Job Application Tracker
"""
        return summary
