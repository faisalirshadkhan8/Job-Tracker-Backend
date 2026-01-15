from rest_framework import serializers
from .models import Interview


class InterviewSerializer(serializers.ModelSerializer):
    """Full serializer for Interview model."""
    company_name = serializers.CharField(source='application.company.name', read_only=True)
    job_title = serializers.CharField(source='application.job_title', read_only=True)
    is_upcoming = serializers.ReadOnlyField()
    
    class Meta:
        model = Interview
        fields = [
            'id', 'application', 'company_name', 'job_title',
            'round_number', 'interview_type',
            'scheduled_at', 'duration_minutes', 'timezone',
            'meeting_link', 'meeting_location',
            'interviewer_names', 'interviewer_titles',
            'status', 'outcome',
            'preparation_notes', 'post_interview_notes', 'questions_asked',
            'is_upcoming', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_application(self, value):
        """Ensure application belongs to the current user."""
        user = self.context['request'].user
        if value.user != user:
            raise serializers.ValidationError("Application not found.")
        return value


class InterviewListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing interviews."""
    company_name = serializers.CharField(source='application.company.name', read_only=True)
    job_title = serializers.CharField(source='application.job_title', read_only=True)
    is_upcoming = serializers.ReadOnlyField()
    
    class Meta:
        model = Interview
        fields = [
            'id', 'company_name', 'job_title',
            'round_number', 'interview_type',
            'scheduled_at', 'duration_minutes',
            'status', 'outcome', 'is_upcoming'
        ]


class InterviewOutcomeSerializer(serializers.ModelSerializer):
    """Serializer for updating interview outcome."""
    
    class Meta:
        model = Interview
        fields = ['status', 'outcome', 'post_interview_notes']
