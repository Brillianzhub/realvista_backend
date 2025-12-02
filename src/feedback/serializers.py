from rest_framework import serializers
from .models import Feedback


class FeedbackSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='user.name', read_only=True)
    avatar = serializers.ImageField(read_only=True)

    class Meta:
        model = Feedback
        fields = ['id', 'name', 'position', 'company',
                  'feedback', 'avatar', 'created_at']
        read_only_fields = ['id', 'name', 'avatar', 'created_at']
