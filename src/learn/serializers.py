from rest_framework import serializers
from .models import Learn


class LearnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Learn
        fields = [
            'id',
            'title',
            'slug',
            'description',
            'category',
            'youtube_url',
            'youtube_id',
            'thumbnail_url',
            'duration',
            'view_count',
            'created_at',
        ]
        read_only_fields = ['slug', 'youtube_id',
                            'thumbnail_url', 'created_at']
