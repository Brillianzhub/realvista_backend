from rest_framework import serializers
from .models import Project, ProjectImage


class ProjectImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProjectImage
        fields = ['image_url']


class ProjectSerializer(serializers.ModelSerializer):
    available_slots = serializers.SerializerMethodField()

    images = ProjectImageSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'project_reference', 'name', 'description', 'budget', 'cost_per_slot', 'num_slots',
                  'location', 'type_of_project', 'status', 'ordered_slots', 'available_slots', 'created_at', 'images']

    def get_available_slots(self, obj):
        return obj.available_slots