from rest_framework import serializers
from .models import Company


class CompanySerializer(serializers.ModelSerializer):
    """Serializer for Company model."""
    application_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'website', 'industry', 'location', 
            'size', 'glassdoor_rating', 'notes', 'application_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Automatically set the user from request
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class CompanyListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing companies."""
    application_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Company
        fields = ['id', 'name', 'industry', 'location', 'application_count']
