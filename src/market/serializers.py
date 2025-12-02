from .models import MarketProperty, MarketCoordinate
from django.db.models import Avg
from .models import MarketPropertyFile
from django.conf import settings
from .models import BookmarkedProperty
from .models import MarketFeatures, MarketProperty, PropertyImage, MarketCoordinate
from rest_framework import serializers
from accounts.models import User
from agents.models import Agent, AgentRating


class MarketCoordinateSerializer(serializers.ModelSerializer):
    utm_x = serializers.FloatField(write_only=True)
    utm_y = serializers.FloatField(write_only=True)
    utm_zone = serializers.IntegerField(write_only=True, default=32)

    latitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, read_only=True)
    longitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, read_only=True)

    class Meta:
        model = MarketCoordinate
        fields = ['id', 'property', 'latitude',
                  'longitude', 'utm_x', 'utm_y', 'utm_zone']

    def create(self, validated_data):
        utm_x = validated_data.pop('utm_x')
        utm_y = validated_data.pop('utm_y')
        utm_zone = validated_data.pop('utm_zone')

        # Convert UTM to WGS84
        latitude, longitude = MarketCoordinate.convert_utm_to_wgs84(
            utm_x, utm_y, utm_zone)

        # Save the MarketCoordinate
        return MarketCoordinate.objects.create(
            latitude=latitude,
            longitude=longitude,
            **validated_data
        )


class SingleMarketCoordinateSerializer(serializers.ModelSerializer):
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
        queryset=MarketProperty.objects.all()
    )

    class Meta:
        model = MarketCoordinate
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
            return MarketCoordinate.objects.create(**validated_data)

        if utm_x is not None and utm_y is not None and utm_zone is not None:
            latitude, longitude = MarketCoordinate.convert_utm_to_wgs84(
                utm_x, utm_y, utm_zone)
            validated_data['latitude'] = latitude
            validated_data['longitude'] = longitude
            return MarketCoordinate.objects.create(**validated_data)

        raise serializers.ValidationError(
            "Either WGS84 or valid UTM coordinates must be provided.")


class MarketCoordinateListSerializer(serializers.Serializer):
    property = serializers.PrimaryKeyRelatedField(
        queryset=MarketProperty.objects.all()
    )
    coordinates = serializers.ListField(
        child=serializers.DictField(),  
    )

    def create(self, validated_data):
        property_instance = validated_data['property']
        coordinates_data = validated_data['coordinates']

        if not coordinates_data:
            raise serializers.ValidationError(
                "Coordinates list cannot be empty.")

        # Only use the first coordinate
        first_coordinate = coordinates_data[0]
        latitude = first_coordinate.get('latitude')
        longitude = first_coordinate.get('longitude')

        if latitude is None or longitude is None:
            raise serializers.ValidationError(
                "Latitude and longitude are required.")

        # Update existing or create
        coordinate, created = MarketCoordinate.objects.update_or_create(
            property=property_instance,
            defaults={'latitude': latitude, 'longitude': longitude},
        )

        return [coordinate]  # return as a list for compatibility with the view


# class MarketCoordinateListSerializer(serializers.Serializer):
#     property = serializers.PrimaryKeyRelatedField(
#         queryset=MarketProperty.objects.all())
#     coordinates = serializers.ListField(
#         child=serializers.DictField()
#     )

#     def create(self, validated_data):
#         property_instance = validated_data['property']
#         coordinates_data = validated_data['coordinates']
#         created_coordinates = []

#         for coordinate_data in coordinates_data:
#             coordinate_data['property'] = property_instance.id
#             serializer = SingleMarketCoordinateSerializer(data=coordinate_data)
#             serializer.is_valid(raise_exception=True)
#             created_coordinates.append(serializer.save())

#         return created_coordinates


class PropertyImageUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ['property', 'image', 'image_url']


class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ['id', 'image', 'image_url', 'uploaded_at']


class MarketPropertyFileSerializer(serializers.ModelSerializer):
    file_type = serializers.SerializerMethodField()

    class Meta:
        model = MarketPropertyFile
        fields = ['id', 'name', 'file',
                  'image_url', 'file_type', 'uploaded_at']

    def get_file_type(self, obj):
        return obj.file_type()


class OwnerSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    owner_bio = serializers.SerializerMethodField()
    owner_rating = serializers.SerializerMethodField()

    email = serializers.EmailField()
    phone_number = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    owner_photo = serializers.SerializerMethodField()

    contact_by_email = serializers.SerializerMethodField()
    contact_by_whatsapp = serializers.SerializerMethodField()
    contact_by_phone = serializers.SerializerMethodField()

    active_since = serializers.SerializerMethodField()
    base_city = serializers.SerializerMethodField()
    base_state = serializers.SerializerMethodField()

    def get_id(self, obj):
        if isinstance(obj, Agent):
            return obj.id
        elif hasattr(obj, 'user') and hasattr(obj.user, 'agent_profile'):
            return obj.user.agent_profile.id
        elif hasattr(obj, 'agent_profile'):
            return obj.agent_profile.id
        return None

    def get_owner_bio(self, obj):
        """Get bio from the Agent model"""
        if isinstance(obj, Agent):
            return obj.bio
        elif hasattr(obj, 'agent_profile'):  # Direct agent profile reference
            return obj.agent_profile.bio
        elif hasattr(obj, 'user') and hasattr(obj.user, 'agent_profile'):  # Through user
            return obj.user.agent_profile.bio
        return None

    def get_owner_rating(self, obj):
        if isinstance(obj, Agent):
            return obj.ratings.aggregate(avg_rating=Avg('rating'))['avg_rating']
        elif hasattr(obj, 'agent_profile'):
            return obj.agent_profile.ratings.aggregate(avg_rating=Avg('rating'))['avg_rating']
        elif hasattr(obj, 'user') and hasattr(obj.user, 'agent_profile'):
            return obj.user.agent_profile.ratings.aggregate(avg_rating=Avg('rating'))['avg_rating']
        return None

    def get_owner_name(self, obj):
        return obj.profile.user.name if hasattr(obj, 'profile') and obj.profile else obj.name

    def get_owner_photo(self, obj):
        if hasattr(obj, 'profile') and obj.profile and obj.profile.avatar:
            return obj.profile.avatar.url if obj.profile.avatar.url else None
        return None

    def get_phone_number(self, obj):
        if hasattr(obj, 'profile') and obj.profile and obj.profile.phone_number:
            return str(obj.profile.phone_number)
        return "N/A"

    def get_active_since(self, obj):
        return obj.profile.user.date_joined if hasattr(obj, 'profile') and obj.profile else obj.date_joined

    def get_base_city(self, obj):
        return obj.profile.city if hasattr(obj, 'profile') and obj.profile else obj.city

    def get_base_state(self, obj):
        return obj.profile.state if hasattr(obj, 'profile') and obj.profile else obj.state

    def get_contact_by_email(self, obj):
        return self._get_preference(obj, 'contact_by_email')

    def get_contact_by_whatsapp(self, obj):
        return self._get_preference(obj, 'contact_by_whatsapp')

    def get_contact_by_phone(self, obj):
        return self._get_preference(obj, 'contact_by_phone')

    def _get_preference(self, obj, field_name):
        if hasattr(obj, 'preferences') and getattr(obj.preferences, field_name, None) is not None:
            return getattr(obj.preferences, field_name)
        return "N/A"


class MarketFeaturesSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketFeatures
        fields = [
            'negotiable',
            'furnished',
            'pet_friendly',
            'parking_available',
            'swimming_pool',
            'garden',
            'electricity_proximity',
            'road_network',
            'development_level',
            'water_supply',
            'security',
            'additional_features',
            'verified_user'
        ]
        read_only_fields = ['verified_user']


class MarketPropertySerializer(serializers.ModelSerializer):
    owner = OwnerSerializer(read_only=True)
    images = PropertyImageSerializer(many=True, read_only=True)
    features = MarketFeaturesSerializer(many=True, read_only=True)
    market_coordinates = serializers.SerializerMethodField()
    image_files = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    videos = serializers.SerializerMethodField()

    class Meta:
        model = MarketProperty
        fields = [
            'id', 'title', 'description', 'property_type', 'price', 'currency',
            'listing_purpose', 'category', 'address', 'city', 'state', 'zip_code', 'availability',
            'availability_date', 'bedrooms', 'bathrooms', 'square_feet', 'lot_size',
            'year_built', 'views', 'inquiries', 'bookmarked', 'listed_date', 'updated_date',
            'coordinate_url', 'images', 'image_files', 'documents', 'videos', 'owner', 'features', 'payment_plans', 'market_coordinates'
        ]

    def validate(self, data):
        if data.get('property_type') == 'land':
            if data.get('bedrooms') is not None:
                raise serializers.ValidationError({
                    'bedrooms': 'Land cannot have bedrooms.'
                })
            if data.get('bathrooms') is not None:
                raise serializers.ValidationError({
                    'bathrooms': 'Land cannot have bathrooms.'
                })

        if data.get('availability') == 'date' and not data.get('availability_date'):
            raise serializers.ValidationError({
                'availability_date': "An availability date must be provided if availability is set to 'Available from Specified Date'."
            })

        return data

    def get_image_files(self, obj):
        images = obj.market_property_files.all()
        return MarketPropertyFileSerializer([file for file in images if file.file_type() == 'image'], many=True).data

    def get_documents(self, obj):
        documents = obj.market_property_files.all()
        return MarketPropertyFileSerializer([file for file in documents if file.file_type() == 'document' or file.file_type() == 'pdf'], many=True).data

    def get_videos(self, obj):
        videos = obj.market_property_files.all()
        return MarketPropertyFileSerializer([file for file in videos if file.file_type() == 'video'], many=True).data

    def get_market_coordinates(self, obj):
        return [
            {
                "id": coordinate.id,
                "latitude": coordinate.latitude,
                "longitude": coordinate.longitude,
            }
            for coordinate in obj.market_coordinates.all()
        ]


def truncate_text(text, limit=150):
    """Shorten long text fields."""
    return text[:limit].rstrip() + "..." if text and len(text) > limit else text


class MarketPropertyListSerializer(serializers.ModelSerializer):
    preview_images = serializers.SerializerMethodField()
    short_description = serializers.SerializerMethodField()

    class Meta:
        model = MarketProperty
        fields = [
            'id',
            'title',
            'city',
            'state',
            'short_description',
            'price',
            'currency',
            'property_type',
            'category',
            'listing_purpose',
            'preview_images',
        ]

    def get_short_description(self, obj):
        """Return truncated version of description."""
        return truncate_text(obj.description, 150)

    def get_preview_images(self, obj):
        """
        Fetch up to 3 image URLs from related market_property_files.
        """
        # assuming model has related_name='market_property_files'
        files = obj.market_property_files.all()
        image_files = [f for f in files if getattr(
            f, "file_type", lambda: "")() == "image"]
        return [f.file.url for f in image_files[:3] if f.file]
