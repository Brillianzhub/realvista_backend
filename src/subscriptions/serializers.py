from rest_framework import serializers
from .models import SubscriptionPlan, PlanDuration, UserSubscription


class PlanDurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanDuration
        fields = [
            "id", "plan", "duration_type", "paystack_plan_code", "price", "currency",
            "discount_percentage", "is_active", "discounted_price"
        ]

        def to_representation(self, instance):
            data = super().to_representation(instance)
            if 'price' in data:
                data['price'] = float(data['price'])
            return data


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    features = serializers.SerializerMethodField()
    durations = PlanDurationSerializer(many=True)

    class Meta:
        model = SubscriptionPlan
        fields = [
            "id", "name", "features", "created_at",
            "color", "popular", "image", "durations"
        ]

    def get_features(self, obj):
        if obj.features:
            return obj.features.split(", ")
        return []


class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan = serializers.CharField(
        source='plan.plan', read_only=True) 
    price = serializers.DecimalField(
        source='plan.price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    currency = serializers.CharField(source='plan.currency', read_only=True)
    next_payment_date = serializers.DateTimeField(
        format="%Y-%m-%d %H:%M:%S",
        required=False,
        allow_null=True
    )

    class Meta:
        model = UserSubscription
        fields = [
            'plan',
            'price',
            'currency',
            'subscription_code',
            'status',
            'next_payment_date'
        ]

    def to_representation(self, instance):
        if not instance:
            return {
                "plan": "free",
                "price": "free",
                "currency": "NGN",
                "next_payment_date": None,
                "subscription_code": None,
                "status": None
            }
        return super().to_representation(instance)
