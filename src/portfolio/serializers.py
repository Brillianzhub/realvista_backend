from rest_framework import serializers
from .models import Property


class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ['id', 'owner', 'location', 'description', 'property_type',
                  'initial_cost', 'current_value', 'area_sqm', 'added_on']
        read_only_fields = ['id', 'added_on']
