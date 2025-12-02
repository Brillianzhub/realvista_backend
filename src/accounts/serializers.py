from decimal import Decimal
from .models import ReferralPayout
from .models import AdminProfile
from agents.serializers import AgentSerializer
from agents.models import Agent
from subscriptions.models import UserSubscription
from phonenumber_field.modelfields import PhoneNumberField
from .models import User, Profile, UserPreference
from rest_framework import serializers
from enterprise.models import CorporateEntity, CorporateEntityMember


class CorporateEntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = CorporateEntity
        fields = ['id', 'name', 'description', 'created_at']


class MembershipSerializer(serializers.ModelSerializer):
    group = CorporateEntitySerializer(source='corporate_entity')
    role = serializers.CharField()

    class Meta:
        model = CorporateEntityMember
        fields = ['group', 'role']


class ProfileSerializer(serializers.ModelSerializer):
    phone_number = PhoneNumberField(error_messages={
        "invalid": "Enter a valid phone number in international format (e.g., +2348000000000)."
    })
    birth_date = serializers.DateField(
        required=False,
        allow_null=True
    )

    class Meta:
        model = Profile
        fields = [
            'avatar',
            'phone_number',
            'country_of_residence',
            'state',
            'city',
            'street',
            'house_number',
            'postal_code',
            'birth_date',
        ]


class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = ['contact_by_email',
                  'contact_by_whatsapp', 'contact_by_phone']


class AdminProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    name = serializers.CharField(source='user.name', read_only=True)

    class Meta:
        model = AdminProfile
        fields = ['id', 'user', 'email', 'name', 'role',
                  'access_level', 'permissions', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    groups = serializers.SerializerMethodField()
    profile = ProfileSerializer()
    preference = UserPreferenceSerializer()
    agent = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'email', 'password', 'app_identifier',
            'groups', 'profile', 'preference', 'subscription',
            'agent'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def get_groups(self, obj):
        memberships = CorporateEntityMember.objects.filter(user=obj)
        return CorporateEntitySerializer(
            [membership.corporate_entity for membership in memberships],
            many=True
        ).data

    def get_agent(self, obj):
        try:
            agent = Agent.objects.get(user=obj)
            return AgentSerializer(agent).data
        except Agent.DoesNotExist:
            return None

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', None)
        preference_data = validated_data.pop('preference', None)

        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            app_identifier=validated_data['app_identifier']
        )

        if profile_data:
            Profile.objects.create(user=user, **profile_data)

        if preference_data:
            UserPreference.objects.create(user=user, **preference_data)

        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        preference_data = validated_data.pop('preference', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if profile_data:
            Profile.objects.update_or_create(
                user=instance, defaults=profile_data)

        if preference_data:
            UserPreference.objects.update_or_create(
                user=instance, defaults=preference_data)

        return instance


class ReferralPayoutRequestSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=Decimal('10.00'))
    payment_method = serializers.ChoiceField(choices=[
        ('bank', 'Bank Transfer'),
        # ('mobile_money', 'Mobile Money'),
        # ('paypal', 'PayPal'),
    ])
    account_details = serializers.CharField(max_length=500)


class ReferralPayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralPayout
        fields = '__all__'
        read_only_fields = ('status', 'processed_at', 'created_at')


class AdminReferralPayoutSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)

    class Meta:
        model = ReferralPayout
        fields = [
            'id', 'user', 'user_email', 'user_name', 'amount',
            'payment_method', 'account_details', 'status',
            'created_at', 'processed_at', 'admin_notes'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'processed_at']
