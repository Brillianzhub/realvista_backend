from rest_framework import serializers
from .models import Property


class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = '__all__'
        read_only_fields = ['id', 'added_on']

    # def validate(self, data):
    #     if data['current_value'] < data['initial_cost']:
    #         raise serializers.ValidationError("Current value must be greater than initial cost")
    #     return data
