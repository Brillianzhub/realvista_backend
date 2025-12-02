# serializers.py
from portfolio.models import CurrencyRate
from rest_framework import serializers
from agents.models import Agent
from market.models import MarketProperty
from accounts.models import User


class HomePageStatsSerializer(serializers.Serializer):
    properties = serializers.SerializerMethodField()
    cities = serializers.SerializerMethodField()
    happy_clients = serializers.SerializerMethodField()
    agents = serializers.SerializerMethodField()

    DEFAULT_PROPERTIES = 1500
    DEFAULT_CITIES = 40
    DEFAULT_HAPPY_CLIENTS = 2000
    DEFAULT_AGENTS = 100

    def get_properties(self, obj):
        actual_count = MarketProperty.objects.count()
        return max(actual_count, self.DEFAULT_PROPERTIES)

    def get_cities(self, obj):
        actual_count = MarketProperty.objects.values('city').distinct().count()
        return max(actual_count, self.DEFAULT_CITIES)

    def get_happy_clients(self, obj):
        total_users = User.objects.count()
        total_agents = Agent.objects.count()
        actual_clients = total_users - total_agents
        return max(actual_clients, self.DEFAULT_HAPPY_CLIENTS)

    def get_agents(self, obj):
        actual_agents = Agent.objects.count()
        return max(actual_agents, self.DEFAULT_AGENTS)


class CurrencyRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrencyRate
        fields = ['id', 'currency_code', 'description', 'rate', 'base']
