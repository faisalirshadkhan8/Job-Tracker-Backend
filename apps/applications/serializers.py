from rest_framework import serializers
from .models import Application, Note, ResumeVersion
from apps.companies.serializers import CompanyListSerializer


class ResumeVersionSerializer(serializers.ModelSerializer):
    """Serializer for resume versions."""
    file = serializers.FileField(write_only=True, required=False)
    file_size_display = serializers.SerializerMethodField()
    
    class Meta:
        model = ResumeVersion
        fields = [
            'id', 'version_name', 'file_url', 'file_name', 'file_size',
            'file_size_display', 'cloudinary_public_id', 'is_default', 
            'created_at', 'file'
        ]
        read_only_fields = ['id', 'file_url', 'file_name', 'file_size', 'cloudinary_public_id', 'created_at']

    def get_file_size_display(self, obj):
        """Return human-readable file size."""
        if obj.file_size < 1024:
            return f"{obj.file_size} B"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.1f} KB"
        else:
            return f"{obj.file_size / (1024 * 1024):.1f} MB"

    def create(self, validated_data):
        file = validated_data.pop('file', None)
        validated_data['user'] = self.context['request'].user
        
        if file:
            from services.cloudinary_service import CloudinaryService
            user = self.context['request'].user
            version_name = validated_data.get('version_name', 'resume')
            
            # Upload to Cloudinary
            result = CloudinaryService.upload_resume(file, user.id, version_name)
            
            validated_data['file_url'] = result['url']
            validated_data['file_name'] = result['filename']
            validated_data['cloudinary_public_id'] = result['public_id']
            validated_data['file_size'] = result['size']
        
        return super().create(validated_data)


class ResumeUploadSerializer(serializers.Serializer):
    """Serializer specifically for resume file upload."""
    file = serializers.FileField(required=True)
    version_name = serializers.CharField(max_length=100, required=True)
    is_default = serializers.BooleanField(default=False)
    
    def validate_file(self, value):
        # Validate file type
        allowed_types = ['application/pdf', 'application/msword', 
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Only PDF and Word documents are allowed.")
        
        # Validate file size (max 5MB)
        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("File size must be less than 5MB.")
        
        return value


class NoteSerializer(serializers.ModelSerializer):
    """Serializer for application notes."""
    
    class Meta:
        model = Note
        fields = ['id', 'content', 'note_type', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ApplicationSerializer(serializers.ModelSerializer):
    """Full serializer for Application model."""
    company_name = serializers.CharField(source='company.name', read_only=True)
    days_since_applied = serializers.ReadOnlyField()
    has_response = serializers.ReadOnlyField()
    notes_count = serializers.SerializerMethodField()
    interviews_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Application
        fields = [
            'id', 'company', 'company_name', 'job_title', 'job_url', 'job_description',
            'status', 'priority', 'work_type', 'location',
            'salary_min', 'salary_max', 'source', 'referrer_name',
            'cover_letter', 'resume_version',
            'applied_date', 'response_date',
            'next_action', 'next_action_date',
            'days_since_applied', 'has_response',
            'notes_count', 'interviews_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_notes_count(self, obj):
        return obj.notes.count()

    def get_interviews_count(self, obj):
        return obj.interviews.count() if hasattr(obj, 'interviews') else 0

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def validate_company(self, value):
        """Ensure company belongs to the current user."""
        user = self.context['request'].user
        if value.user != user:
            raise serializers.ValidationError("Company not found.")
        return value


class ApplicationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing applications."""
    company_name = serializers.CharField(source='company.name', read_only=True)
    days_since_applied = serializers.ReadOnlyField()
    
    class Meta:
        model = Application
        fields = [
            'id', 'company', 'company_name', 'job_title', 
            'status', 'priority', 'work_type', 'location',
            'source', 'applied_date', 'days_since_applied', 'updated_at'
        ]


class ApplicationDetailSerializer(ApplicationSerializer):
    """Detailed serializer including nested notes."""
    notes = NoteSerializer(many=True, read_only=True)
    company_details = CompanyListSerializer(source='company', read_only=True)
    
    class Meta(ApplicationSerializer.Meta):
        fields = ApplicationSerializer.Meta.fields + ['notes', 'company_details']


class ApplicationStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for quick status updates."""
    
    class Meta:
        model = Application
        fields = ['status', 'response_date']
