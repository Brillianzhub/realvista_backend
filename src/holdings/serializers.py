from rest_framework import serializers
from .models import Holding
from projects.serializers import ProjectSerializer


class HoldingSerializer(serializers.ModelSerializer):
    project = ProjectSerializer(read_only=True)

    class Meta:
        model = Holding
        fields = [
            'id', 'amount', 'project', 'slots', 'created_at'
        ]
