from .models import InstallmentPayment, PropertyPurchase
from decimal import Decimal
from django.core.exceptions import ValidationError
from rest_framework import serializers
from .models import PropertyPurchase, InstallmentPayment

from .models import PaymentPlan

class PaymentPlanSerializer(serializers.ModelSerializer):
    name_display = serializers.SerializerMethodField()

    class Meta:
        model = PaymentPlan
        fields = ['id', 'name', 'name_display', 'duration_months', 'interest_rate']
        read_only_fields = ['duration_months']

    def get_name_display(self, obj):
        """Returns the human-readable name for the selected plan."""
        return dict(PaymentPlan.PLAN_CHOICES).get(obj.name, obj.name)


class PropertyPurchaseSerializer(serializers.ModelSerializer):
    total_amount = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True)
    remaining_balance = serializers.SerializerMethodField()
    monthly_installment = serializers.SerializerMethodField()

    class Meta:
        model = PropertyPurchase
        fields = ['id', 'user', 'property', 'payment_plan', 'amount_paid', 'status',
                  'created_at', 'total_amount', 'currency', 'remaining_balance', 'monthly_installment']
        read_only_fields = ['id', 'total_amount', 'currency', 'created_at',
                            'remaining_balance', 'monthly_installment']

    def get_remaining_balance(self, obj):
        return obj.remaining_balance()

    def get_monthly_installment(self, obj):
        return obj.monthly_installment()


class InstallmentPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstallmentPayment
        fields = ['id', 'purchase', 'amount', 'timestamp']

    def validate(self, data):
        purchase = data['purchase']
        amount = Decimal(data['amount'])

        if purchase.status == 'completed':
            raise serializers.ValidationError(
                {"error": "This purchase is already fully paid."}
            )

        if purchase.status == 'canceled':
            raise serializers.ValidationError(
                {"error": "Payments cannot be made for a canceled purchase."}
            )

        if amount <= 0:
            raise serializers.ValidationError(
                {"error": "Payment amount must be greater than zero."}
            )

        if amount > purchase.remaining_balance():
            raise serializers.ValidationError(
                {"error": "Payment amount exceeds the remaining balance."}
            )

        return data

    def create(self, validated_data):
        purchase = validated_data['purchase']
        amount = validated_data['amount']

        purchase.apply_payment(amount)

        return super().create(validated_data)
