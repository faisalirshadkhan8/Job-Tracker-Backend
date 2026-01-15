"""
AI Serializers - Input validation and output formatting.
"""

from rest_framework import serializers

from .models import AITask, GeneratedContent


class ApplicationIdValidationMixin:
    """Validate application_id belongs to the authenticated user."""

    def _validate_application_id(self, data):
        application_id = data.get("application_id")
        if not application_id:
            return data

        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            raise serializers.ValidationError("Request context with authenticated user is required.")

        from apps.applications.models import Application

        exists = Application.objects.filter(id=application_id, user=request.user).exists()
        if not exists:
            raise serializers.ValidationError("Invalid application_id for this user.")

        return data


# ============== AI Task Serializers ==============


class AITaskSerializer(serializers.ModelSerializer):
    """Serializer for AI task status tracking."""

    task_type_display = serializers.CharField(source="get_task_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    duration = serializers.FloatField(read_only=True)

    class Meta:
        model = AITask
        fields = [
            "id",
            "task_type",
            "task_type_display",
            "status",
            "status_display",
            "created_at",
            "started_at",
            "completed_at",
            "duration",
        ]
        read_only_fields = fields


class AITaskDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with result/error."""

    task_type_display = serializers.CharField(source="get_task_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    duration = serializers.FloatField(read_only=True)

    class Meta:
        model = AITask
        fields = [
            "id",
            "task_type",
            "task_type_display",
            "status",
            "status_display",
            "input_params",
            "result",
            "error_message",
            "created_at",
            "started_at",
            "completed_at",
            "duration",
        ]
        read_only_fields = fields


class AsyncResponseSerializer(serializers.Serializer):
    """Response for async task creation."""

    task_id = serializers.IntegerField(help_text="ID to poll for status")
    status = serializers.CharField(help_text="Current task status")
    message = serializers.CharField(help_text="User-friendly message")


# ============== Cover Letter Serializers ==============


class CoverLetterInputSerializer(ApplicationIdValidationMixin, serializers.Serializer):
    """Input for cover letter generation."""

    TONE_CHOICES = [
        ("professional", "Professional"),
        ("enthusiastic", "Enthusiastic"),
        ("formal", "Formal"),
        ("conversational", "Conversational"),
    ]

    job_description = serializers.CharField(
        required=True, min_length=50, help_text="The full job posting text (min 50 characters)"
    )
    resume_text = serializers.CharField(
        required=False, help_text="Resume text. Required if resume_version_id not provided."
    )
    resume_version_id = serializers.IntegerField(required=False, help_text="ID of a saved resume version to use")
    company_name = serializers.CharField(required=True, max_length=255, help_text="Name of the company")
    job_title = serializers.CharField(required=True, max_length=255, help_text="Title of the position")
    tone = serializers.ChoiceField(
        choices=TONE_CHOICES, default="professional", help_text="Writing tone for the cover letter"
    )
    application_id = serializers.IntegerField(required=False, help_text="Optional: Link to an existing application")
    save_to_history = serializers.BooleanField(default=True, help_text="Whether to save this generation to history")
    async_mode = serializers.BooleanField(
        required=False,
        default=None,
        help_text="Run asynchronously (returns task_id for polling). Defaults to server setting.",
    )

    def validate(self, data):
        """Ensure either resume_text or resume_version_id is provided."""
        if not data.get("resume_text") and not data.get("resume_version_id"):
            raise serializers.ValidationError("Either 'resume_text' or 'resume_version_id' must be provided.")
        return self._validate_application_id(data)


class CoverLetterOutputSerializer(serializers.Serializer):
    """Output from cover letter generation."""

    cover_letter = serializers.CharField()
    model = serializers.CharField()
    tokens_used = serializers.IntegerField()
    saved_id = serializers.IntegerField(required=False, allow_null=True)


class JobMatchInputSerializer(ApplicationIdValidationMixin, serializers.Serializer):
    """Input for job match analysis."""

    job_description = serializers.CharField(required=True, min_length=50, help_text="The full job posting text")
    resume_text = serializers.CharField(
        required=False, help_text="Resume text. Required if resume_version_id not provided."
    )
    resume_version_id = serializers.IntegerField(required=False, help_text="ID of a saved resume version to use")
    application_id = serializers.IntegerField(required=False, help_text="Optional: Link to an existing application")
    save_to_history = serializers.BooleanField(default=True, help_text="Whether to save this analysis to history")
    async_mode = serializers.BooleanField(
        required=False,
        default=None,
        help_text="Run asynchronously (returns task_id for polling). Defaults to server setting.",
    )

    def validate(self, data):
        if not data.get("resume_text") and not data.get("resume_version_id"):
            raise serializers.ValidationError("Either 'resume_text' or 'resume_version_id' must be provided.")
        return self._validate_application_id(data)


class JobMatchOutputSerializer(serializers.Serializer):
    """Output from job match analysis."""

    analysis = serializers.JSONField()
    model = serializers.CharField()
    tokens_used = serializers.IntegerField()
    saved_id = serializers.IntegerField(required=False, allow_null=True)


class InterviewQuestionsInputSerializer(ApplicationIdValidationMixin, serializers.Serializer):
    """Input for interview question generation."""

    job_description = serializers.CharField(required=True, min_length=50, help_text="The full job posting text")
    company_name = serializers.CharField(required=True, max_length=255, help_text="Name of the company")
    job_title = serializers.CharField(required=True, max_length=255, help_text="Title of the position")
    question_count = serializers.IntegerField(
        default=10, min_value=5, max_value=20, help_text="Number of questions to generate (5-20)"
    )
    application_id = serializers.IntegerField(required=False, help_text="Optional: Link to an existing application")
    save_to_history = serializers.BooleanField(default=True, help_text="Whether to save to history")
    async_mode = serializers.BooleanField(
        required=False,
        default=None,
        help_text="Run asynchronously (returns task_id for polling). Defaults to server setting.",
    )

    def validate(self, data):
        return self._validate_application_id(data)


class InterviewQuestionsOutputSerializer(serializers.Serializer):
    """Output from interview question generation."""

    questions = serializers.CharField()
    model = serializers.CharField()
    tokens_used = serializers.IntegerField()
    saved_id = serializers.IntegerField(required=False, allow_null=True)


class GeneratedContentSerializer(serializers.ModelSerializer):
    """Serializer for saved generated content history."""

    content_type_display = serializers.CharField(source="get_content_type_display", read_only=True)

    class Meta:
        model = GeneratedContent
        fields = [
            "id",
            "content_type",
            "content_type_display",
            "input_company_name",
            "input_job_title",
            "output_content",
            "model_used",
            "tokens_used",
            "is_favorite",
            "rating",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class GeneratedContentDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with all input/output data."""

    content_type_display = serializers.CharField(source="get_content_type_display", read_only=True)

    class Meta:
        model = GeneratedContent
        fields = "__all__"
        read_only_fields = ["id", "user", "created_at"]
