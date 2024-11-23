from rest_framework import serializers
from .models import Order
from projects.serializers import ProjectSerializer


class OrderSerializer(serializers.ModelSerializer):
    project = ProjectSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'quantity', 'project', 'total_amount',
            'payment_status', 'order_reference', 'created_at', 'updated_at'
        ]
