from .models import AgentVerification
from django.db import models
from rest_framework import serializers
from .models import Agent, AgentRating
from market.models import MarketProperty
from accounts.models import User

from rest_framework import serializers
from .models import AgentRating


class AgentRatingSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(
        source='user.name', read_only=True)

    class Meta:
        model = AgentRating
        fields = ['id', 'agent', 'rating', 'review',
                  'created_at', 'updated_at', 'user_name']
        read_only_fields = ['created_at', 'updated_at', 'user_name']

    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user
        agent = attrs.get('agent')

        if self.instance is None and AgentRating.objects.filter(user=user, agent=agent).exists():
            raise serializers.ValidationError(
                "You have already rated this agent.")
        return attrs

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class MarketPropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketProperty
        fields = [
            'id',
            'title',
            'price',
            'currency',
            'address',
            'city',
            'state',
            'images',
            'property_type',
            'listed_date',
        ]
        read_only_fields = ['listed_date']


class MarketPropertyStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketProperty
        fields = [
            'id',
            'title',
            'price',
            'currency',
            'address',
            'city',
            'state',
            'images',
            'views',
            'inquiries',
            'bookmarked',
            'property_type',
            'listed_date',
        ]
        read_only_fields = ['listed_date']


class AgentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    properties = serializers.SerializerMethodField()
    ratings = AgentRatingSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Agent
        fields = [
            'id',
            'user',
            'avatar',
            'agency_name',
            'agency_address',
            'phone_number',
            'whatsapp_number',
            'experience_years',
            'preferred_contact_mode',
            'verified',
            'featured',
            'bio',
            'created_at',
            'updated_at',
            'properties',
            'ratings',
            'average_rating'
        ]
        read_only_fields = ['verified', 'featured', 'created_at', 'updated_at']

    def get_properties(self, obj):
        properties = MarketProperty.objects.filter(owner=obj.user)
        return MarketPropertySerializer(properties, many=True).data

    def get_average_rating(self, obj):
        return obj.ratings.aggregate(models.Avg('rating'))['rating__avg']


class AgentStatSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    properties = serializers.SerializerMethodField()
    ratings = AgentRatingSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()

    total_views = serializers.SerializerMethodField()
    total_inquiries = serializers.SerializerMethodField()
    total_bookmarks = serializers.SerializerMethodField()
    total_listings = serializers.SerializerMethodField()
    top_performing_properties = serializers.SerializerMethodField()

    class Meta:
        model = Agent
        fields = [
            'id',
            'user',
            'avatar',
            'agency_name',
            'agency_address',
            'phone_number',
            'whatsapp_number',
            'experience_years',
            'preferred_contact_mode',
            'verified',
            'featured',
            'bio',
            'created_at',
            'updated_at',
            'properties',
            'ratings',
            'average_rating',
            'total_views',
            'total_inquiries',
            'total_bookmarks',
            'total_listings',
            'top_performing_properties'
        ]
        read_only_fields = ['verified', 'featured', 'created_at', 'updated_at']

    def get_properties(self, obj):
        properties = MarketProperty.objects.filter(owner=obj.user)
        return MarketPropertyStatSerializer(properties, many=True).data

    def get_average_rating(self, obj):
        return obj.ratings.aggregate(models.Avg('rating'))['rating__avg']

    def get_total_views(self, obj):
        properties = MarketProperty.objects.filter(owner=obj.user)
        return properties.aggregate(total_views=models.Sum('views'))['total_views'] or 0

    def get_total_inquiries(self, obj):
        properties = MarketProperty.objects.filter(owner=obj.user)
        return properties.aggregate(total_inquiries=models.Sum('inquiries'))['total_inquiries'] or 0

    def get_total_bookmarks(self, obj):
        properties = MarketProperty.objects.filter(owner=obj.user)
        return properties.aggregate(total_bookmarks=models.Sum('bookmarked'))['total_bookmarks'] or 0

    def get_total_listings(self, obj):
        return MarketProperty.objects.filter(owner=obj.user).count()

    def get_top_performing_properties(self, obj):
        properties = MarketProperty.objects.filter(owner=obj.user).annotate(
            engagement=models.F('views') +
            models.F('inquiries') + models.F('bookmarked')
        ).order_by('-engagement')[:3]
        return MarketPropertySerializer(properties, many=True).data


class AgentVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentVerification
        fields = [
            'id', 'id_card', 'photo', 'business_registration',
            'submitted_at', 'reviewed', 'approved', 'rejection_reason'
        ]
        read_only_fields = [
            'submitted_at', 'reviewed', 'approved', 'rejection_reason'
        ]
