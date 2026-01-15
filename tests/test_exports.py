"""
Tests for Export functionality.
"""

from io import BytesIO
from zipfile import ZipFile

from django.urls import reverse

from rest_framework import status

import pytest

from apps.applications.models import Application
from apps.companies.models import Company
from apps.interviews.models import Interview


@pytest.fixture
def export_data(user, auth_client):
    """Create sample data for exports."""
    # Create companies
    company1 = Company.objects.create(
        user=user, name="Tech Corp", website="https://techcorp.com", industry="Technology"
    )
    company2 = Company.objects.create(user=user, name="Data Inc", website="https://datainc.com", industry="Data")

    # Create applications
    app1 = Application.objects.create(
        user=user, company=company1, job_title="Software Engineer", status="applied", location="Remote"
    )
    app2 = Application.objects.create(
        user=user, company=company2, job_title="Data Scientist", status="interviewing", location="NYC"
    )

    # Create interviews
    from django.utils import timezone

    Interview.objects.create(application=app1, interview_type="phone", status="scheduled", scheduled_at=timezone.now())

    return {
        "companies": [company1, company2],
        "applications": [app1, app2],
    }


@pytest.mark.django_db
class TestExportApplications:
    """Tests for application exports."""

    def test_export_applications_csv(self, auth_client, user, export_data):
        """Test exporting applications to CSV."""
        url = reverse("export-applications")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "text/csv"
        assert "attachment" in response["Content-Disposition"]
        assert "applications" in response["Content-Disposition"]

        content = response.content.decode("utf-8")
        assert "Software Engineer" in content
        assert "Data Scientist" in content
        assert "Tech Corp" in content

    def test_export_applications_with_status_filter(self, auth_client, user, export_data):
        """Test exporting applications with status filter."""
        url = reverse("export-applications") + "?status=applied"
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        content = response.content.decode("utf-8")
        assert "Software Engineer" in content
        # Data Scientist is "interviewing", should not be in export
        lines = content.strip().split("\n")
        assert len(lines) == 2  # Header + 1 row

    def test_export_applications_unauthenticated(self, api_client):
        """Test export requires authentication."""
        api_client.credentials()  # Clear credentials
        url = reverse("export-applications")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestExportCompanies:
    """Tests for company exports."""

    def test_export_companies_csv(self, auth_client, user, export_data):
        """Test exporting companies to CSV."""
        url = reverse("export-companies")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "text/csv"

        content = response.content.decode("utf-8")
        assert "Tech Corp" in content
        assert "Data Inc" in content


@pytest.mark.django_db
class TestExportInterviews:
    """Tests for interview exports."""

    def test_export_interviews_csv(self, auth_client, user, export_data):
        """Test exporting interviews to CSV."""
        url = reverse("export-interviews")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "text/csv"

        content = response.content.decode("utf-8")
        assert "phone" in content.lower()


@pytest.mark.django_db
class TestExportFullReport:
    """Tests for full report export."""

    def test_export_full_report_zip(self, auth_client, user, export_data):
        """Test exporting full report as ZIP."""
        url = reverse("export-full-report")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "application/zip"

        # Verify it's a valid ZIP with expected files
        zip_buffer = BytesIO(response.content)
        with ZipFile(zip_buffer) as zf:
            names = zf.namelist()
            assert "applications.csv" in names
            assert "companies.csv" in names
            assert "interviews.csv" in names
            assert "summary.txt" in names

    def test_export_full_report_empty(self, auth_client, user):
        """Test exporting full report with no data."""
        url = reverse("export-full-report")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
