from rest_framework import serializers
from .models import Device, Lead


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['id', 'user', 'token', 'created_at']
        read_only_fields = ['id', 'created_at']


class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = '__all__'