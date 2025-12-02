from rest_framework import serializers
from .models import FinancialTarget, Contribution


class ContributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contribution
        fields = ['id', 'amount', 'date', 'created_at']
        read_only_fields = ['created_at']


class FinancialTargetSerializer(serializers.ModelSerializer):
    progress_percentage = serializers.SerializerMethodField()
    remaining_amount = serializers.SerializerMethodField()
    months_remaining = serializers.SerializerMethodField()
    contributions = ContributionSerializer(many=True, read_only=True)
    minimum_monthly_contribution = serializers.SerializerMethodField()

    class Meta:
        model = FinancialTarget
        fields = [
            'id',
            'user',
            'target_name',
            'target_amount',
            'current_savings',
            'start_date',
            'end_date',
            'currency',
            'achieved_at',
            'timeframe',
            'progress_percentage',
            'remaining_amount',
            'months_remaining',
            'minimum_monthly_contribution',
            'contributions',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'progress_percentage', 'remaining_amount', 'months_remaining',
            'minimum_monthly_contribution', 'achieved_at', 'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        # Remove start_date and end_date if they are not provided
        validated_data.pop('start_date', None)
        validated_data.pop('end_date', None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Remove start_date and end_date if they are not provided
        validated_data.pop('start_date', None)
        validated_data.pop('end_date', None)
        return super().update(instance, validated_data)

    def get_progress_percentage(self, obj):
        return obj.calculate_progress_percentage()

    def get_remaining_amount(self, obj):
        return obj.calculate_remaining_amount()

    def get_months_remaining(self, obj):
        return obj.calculate_months_remaining()

    def get_minimum_monthly_contribution(self, obj):
        return obj.calculate_min_monthly_contribution()
