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

    def validate(self, data):
        project = data['project']
        quantity = data['quantity']

        if quantity > project.available_slots:
            raise serializers.ValidationError(
                f"Only {project.available_slots} slots are available for project {project.name}."
            )
        return data
