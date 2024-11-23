from rest_framework import serializers
from .models import Project, ProjectImage


class ProjectImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectImage
        fields = ['image_url']


class ProjectSerializer(serializers.ModelSerializer):
    images = ProjectImageSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'project_reference', 'name', 'description', 'budget', 'cost_per_slot', 'num_slots',
                  'location', 'type_of_project', 'status', 'created_at', 'images']
