from .models import ReleasedSlot
from .models import GroupCoordinate
from .models import GroupProperty, GroupIncome, GroupExpenses, GroupSlotAllocation, GroupPropertyImage, GroupPropertyFile
from rest_framework import serializers
from .models import CorporateEntity, CorporateEntityMember
from django.db.models import Sum
from decimal import Decimal


class GroupPropertyImageUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupPropertyImage
        fields = ['property', 'image']


class GroupPropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupPropertyImage
        fields = ['image', 'uploaded_at']


class GroupPropertyFileSerializer(serializers.ModelSerializer):
    file_type = serializers.SerializerMethodField()

    class Meta:
        model = GroupPropertyFile
        fields = ['id', 'name', 'file', 'file_type', 'uploaded_at']

    def get_file_type(self, obj):
        return obj.file_type()


class CorporateEntitySerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    created_at = serializers.DateTimeField(
        format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = CorporateEntity
        fields = ['id', 'name', 'description',
                  'group_id', 'created_by', 'created_at']


class MembershipSerializer(serializers.ModelSerializer):
    group = CorporateEntitySerializer(source='corporate_entity')
    role = serializers.CharField()

    class Meta:
        model = CorporateEntityMember
        fields = ['group', 'role']


class GroupMemberSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    name = serializers.CharField(source='user.name', read_only=True)
    user_avatar = serializers.SerializerMethodField()

    class Meta:
        model = CorporateEntityMember
        fields = ['id', 'email', 'name', 'user_avatar', 'role', 'joined_at']

    def get_user_avatar(self, obj):
        profile = getattr(obj.user, 'profile', None)
        if profile and profile.avatar:
            return profile.avatar.url
        return None


class GroupIncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupIncome
        fields = ['id', 'amount', 'description', 'date_received']
        read_only_fields = ['id']


class GroupExpensesSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupExpenses
        fields = ['id', 'amount', 'description', 'date_incurred']
        read_only_fields = ['id']


class GroupPropertySerializer(serializers.ModelSerializer):
    appreciation = serializers.SerializerMethodField()
    available_slots = serializers.SerializerMethodField()
    images = GroupPropertyImageSerializer(many=True, read_only=True)
    coordinates = serializers.SerializerMethodField()
    group_owner_name = serializers.SerializerMethodField()
    files = GroupPropertyFileSerializer(
        many=True, read_only=True, source='group_property_files')

    class Meta:
        model = GroupProperty
        fields = [
            'id', 'group_owner', 'group_owner_name', 'title', 'address', 'city', 'location', 'zip_code', 'description',
            'status', 'property_type', 'year_bought', 'area', 'num_units',
            'initial_cost', 'current_value', 'files', 'coordinates', 'currency', 'virtual_tour_url', 'added_on',
            'total_slots', 'slot_price', 'slot_price_current', 'appreciation', 'images', 'available_slots',
        ]
        read_only_fields = [
            'id', 'added_on', 'slot_price', 'slot_price_current', 'appreciation', 'available_slots',
        ]

    def get_appreciation(self, obj):
        return obj.appreciation()

    def get_available_slots(self, obj):
        return obj.available_slots()

    def get_group_owner_name(self, obj):
        return obj.group_owner.name if obj.group_owner else None

    def get_coordinates(self, obj):
        return [
            {
                "id": coordinate.id,
                "latitude": coordinate.latitude,
                "longitude": coordinate.longitude,
            }
            for coordinate in obj.group_coordinates.all()
        ]

    def validate_total_slots(self, value):
        if self.instance:
            allocated_slots = self.instance.slot_allocations.aggregate(
                total=Sum('slots_owned')
            )['total'] or 0
            if value < allocated_slots:
                raise serializers.ValidationError(
                    f"Total slots cannot be less than allocated slots ({allocated_slots})."
                )
        return value

    def create(self, validated_data):
        total_slots = validated_data.get('total_slots', 1) or 1
        initial_cost = validated_data.get('initial_cost', 0)
        current_value = validated_data.get('current_value', 0)

        validated_data['slot_price'] = initial_cost / Decimal(total_slots)
        validated_data['slot_price_current'] = current_value / \
            Decimal(total_slots)

        return super().create(validated_data)

    def update(self, instance, validated_data):
        total_slots = validated_data.get('total_slots', instance.total_slots)
        initial_cost = validated_data.get(
            'initial_cost', instance.initial_cost)
        current_value = validated_data.get(
            'current_value', instance.current_value)

        if 'initial_cost' in validated_data or 'total_slots' in validated_data:
            validated_data['slot_price'] = initial_cost / Decimal(total_slots)

        if 'current_value' in validated_data or 'total_slots' in validated_data:
            validated_data['slot_price_current'] = current_value / \
                Decimal(total_slots)

        return super().update(instance, validated_data)


class GroupSlotAllocationSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    user_name = serializers.SerializerMethodField()
    property = serializers.StringRelatedField(read_only=True)
    total_cost = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = GroupSlotAllocation
        fields = [
            'id',
            'property',
            'user',
            'user_name',
            'slots_owned',
            'total_cost',
            'booking_reference',
            'status',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'total_cost', 'status']

    def get_user_name(self, obj):
        return obj.user.name or obj.user.email

    def create(self, validated_data):
        property = self.context.get('property')
        user = self.context.get('user')
        slots_owned = validated_data.get('slots_owned')

        if slots_owned is None:
            raise serializers.ValidationError(
                {"slots_owned": "This field is required."})

        if property.available_slots is None:
            raise serializers.ValidationError({
                "error": "Group property does not have available slots information."
            })

        if slots_owned > property.available_slots:
            raise serializers.ValidationError({
                "slots_owned": "The requested number of slots exceeds available slots."
            })

        property.available_slots -= slots_owned
        property.save()

        total_cost = slots_owned * property.slot_price

        return GroupSlotAllocation.objects.create(
            property=property,
            user=user,
            slots_owned=slots_owned,
            total_cost=total_cost,
        )


class CoordinateSerializer(serializers.ModelSerializer):
    utm_x = serializers.FloatField(write_only=True)
    utm_y = serializers.FloatField(write_only=True)
    utm_zone = serializers.IntegerField(write_only=True, default=32)

    latitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, read_only=True)
    longitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, read_only=True)

    class Meta:
        model = GroupCoordinate
        fields = ['id', 'property', 'latitude',
                  'longitude', 'utm_x', 'utm_y', 'utm_zone']

    def create(self, validated_data):
        utm_x = validated_data.pop('utm_x')
        utm_y = validated_data.pop('utm_y')
        utm_zone = validated_data.pop('utm_zone')

        # Convert UTM to WGS84
        latitude, longitude = GroupCoordinate.convert_utm_to_wgs84(
            utm_x, utm_y, utm_zone)

        return GroupCoordinate.objects.create(
            latitude=latitude,
            longitude=longitude,
            **validated_data
        )


class SingleCoordinateSerializer(serializers.ModelSerializer):
    utm_x = serializers.FloatField(write_only=True, required=False)
    utm_y = serializers.FloatField(write_only=True, required=False)
    utm_zone = serializers.IntegerField(
        write_only=True, default=32, required=False)

    latitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False
    )
    longitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False
    )

    property = serializers.PrimaryKeyRelatedField(
        queryset=GroupProperty.objects.all()
    )

    class Meta:
        model = GroupCoordinate
        fields = ['property', 'latitude',
                  'longitude', 'utm_x', 'utm_y', 'utm_zone']

    def validate(self, data):
        if ('latitude' in data and 'longitude' in data) or ('utm_x' in data and 'utm_y' in data):
            return data
        raise serializers.ValidationError(
            "Either WGS84 or UTM coordinates must be provided.")

    def create(self, validated_data):
        utm_x = validated_data.pop('utm_x', None)
        utm_y = validated_data.pop('utm_y', None)
        utm_zone = validated_data.pop('utm_zone', None)

        if 'latitude' in validated_data and 'longitude' in validated_data:
            return GroupCoordinate.objects.create(**validated_data)

        if utm_x is not None and utm_y is not None and utm_zone is not None:
            latitude, longitude = GroupCoordinate.convert_utm_to_wgs84(
                utm_x, utm_y, utm_zone)
            validated_data['latitude'] = latitude
            validated_data['longitude'] = longitude
            return GroupCoordinate.objects.create(**validated_data)

        raise serializers.ValidationError(
            "Either WGS84 or valid UTM coordinates must be provided.")


class CoordinateListSerializer(serializers.Serializer):
    property = serializers.PrimaryKeyRelatedField(
        queryset=GroupProperty.objects.all())
    coordinates = serializers.ListField(
        child=serializers.DictField()
    )

    def create(self, validated_data):
        property_instance = validated_data['property']
        coordinates_data = validated_data['coordinates']
        created_coordinates = []

        for coordinate_data in coordinates_data:
            coordinate_data['property'] = property_instance.id
            serializer = SingleCoordinateSerializer(data=coordinate_data)
            serializer.is_valid(raise_exception=True)
            created_coordinates.append(serializer.save())

        return created_coordinates


class GetReleasedSlotSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    property = serializers.StringRelatedField()
    group = serializers.StringRelatedField()
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = ReleasedSlot
        fields = [
            'id', 'user', 'user_name', 'property', 'group',
            'number_of_slots', 'released_at', 'is_available'
        ]
        read_only_fields = ['id', 'released_at', 'user']

    def get_user_name(self, obj):
        return obj.user.name


class ReleasedSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReleasedSlot
        fields = ['id', 'user', 'property', 'group',
                  'number_of_slots', 'released_at', 'is_available']
        read_only_fields = ['id', 'released_at', 'user']
