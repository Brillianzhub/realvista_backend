from rest_framework import serializers
from .models import BoostPackage, BoostOrder

class BoostPackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoostPackage
        fields = ["id", "name", "duration_days", "price"]

class BoostOrderSerializer(serializers.ModelSerializer):
    package = BoostPackageSerializer(read_only=True)
    package_id = serializers.PrimaryKeyRelatedField(
        queryset=BoostPackage.objects.all(), source="package", write_only=True
    )

    class Meta:
        model = BoostOrder
        fields = [
            "id", "user", "property", "package", "package_id",
            "payment_status", "is_active", "starts_at", "ends_at", "transaction_reference"
        ]
        read_only_fields = ["is_active", "starts_at", "ends_at"]
