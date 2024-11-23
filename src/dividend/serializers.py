from rest_framework import serializers

from .models import Dividend, DividendShare


class DividendShareSerializer(serializers.ModelSerializer):
    class Meta:
        model = DividendShare
        fields = ['user', 'share_amount',
                  'retention_percentage', 'final_share_amount']


class DividendSerializer(serializers.ModelSerializer):
    shares = DividendShareSerializer(many=True, read_only=True)

    class Meta:
        model = Dividend
        fields = ['id', 'project', 'total_return',
                  'total_expenses', 'month', 'shares']
