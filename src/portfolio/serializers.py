from .utils import get_performance_data
from .models import PropertyValueHistory
from decimal import Decimal
from rest_framework import serializers
from .models import Property, Income, Expenses, PortfolioPropertyImage
from enterprise.models import GroupProperty, CorporateEntity
from .models import PortfolioPropertyFile


from rest_framework import serializers
from .models import Coordinate


class PortfolioPropertyImageUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioPropertyImage
        fields = ['property', 'image']


class PortfolioPropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioPropertyImage
        fields = ['image', 'uploaded_at']


class PortfolioPropertyFileSerializer(serializers.ModelSerializer):
    file_type = serializers.SerializerMethodField()

    class Meta:
        model = PortfolioPropertyFile
        fields = ['id', 'name', 'file', 'file_type', 'uploaded_at']

    def get_file_type(self, obj):
        return obj.file_type()


class CoordinateSerializer(serializers.ModelSerializer):
    utm_x = serializers.FloatField(write_only=True)
    utm_y = serializers.FloatField(write_only=True)
    utm_zone = serializers.IntegerField(write_only=True, default=32)

    latitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, read_only=True)
    longitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, read_only=True)

    class Meta:
        model = Coordinate
        fields = ['id', 'property', 'latitude',
                  'longitude', 'utm_x', 'utm_y', 'utm_zone']

    def create(self, validated_data):
        utm_x = validated_data.pop('utm_x')
        utm_y = validated_data.pop('utm_y')
        utm_zone = validated_data.pop('utm_zone')

        # Convert UTM to WGS84
        latitude, longitude = Coordinate.convert_utm_to_wgs84(
            utm_x, utm_y, utm_zone)

        # Save the coordinate
        return Coordinate.objects.create(
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
        queryset=Property.objects.all()
    )

    class Meta:
        model = Coordinate
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
            return Coordinate.objects.create(**validated_data)

        if utm_x is not None and utm_y is not None and utm_zone is not None:
            latitude, longitude = Coordinate.convert_utm_to_wgs84(
                utm_x, utm_y, utm_zone)
            validated_data['latitude'] = latitude
            validated_data['longitude'] = longitude
            return Coordinate.objects.create(**validated_data)

        raise serializers.ValidationError(
            "Either WGS84 or valid UTM coordinates must be provided.")


class CoordinateListSerializer(serializers.Serializer):
    property = serializers.PrimaryKeyRelatedField(
        queryset=Property.objects.all())
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


class IncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Income
        fields = ['id', 'property', 'amount',
                  'currency', 'description', 'date_received']

    def validate(self, data):
        if data['amount'] <= 0:
            raise serializers.ValidationError(
                "Income amount must be greater than 0.")
        return data


class ExpensesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expenses
        fields = ['id', 'property', 'amount',
                  'currency', 'description', 'date_incurred']

    def validate(self, data):
        if data['amount'] <= 0:
            raise serializers.ValidationError(
                "Expense amount must be greater than 0.")
        return data


class PropertyValueHistorySerializer(serializers.ModelSerializer):
    property_title = serializers.CharField(
        source='property.title', read_only=True)

    class Meta:
        model = PropertyValueHistory
        fields = ['id', 'property', 'property_title', 'value', 'recorded_at']


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = CorporateEntity
        fields = ['id', 'name']


class GroupPropertySerializer(serializers.ModelSerializer):
    group_owner = GroupSerializer()

    class Meta:
        model = GroupProperty
        fields = ['id', 'group_owner']


class PropertySerializer(serializers.ModelSerializer):
    group_property_id = serializers.SerializerMethodField()
    group_owner_name = serializers.SerializerMethodField()
    incomes = IncomeSerializer(many=True, read_only=True)
    expenses = ExpensesSerializer(many=True, read_only=True)
    available_slots = serializers.SerializerMethodField()
    appreciation = serializers.SerializerMethodField()
    roi = serializers.SerializerMethodField()
    percentage_performance = serializers.SerializerMethodField()
    coordinates = serializers.SerializerMethodField()
    images = PortfolioPropertyImageSerializer(
        many=True, read_only=True, source='portfolio_property_images')
    image_files = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    videos = serializers.SerializerMethodField()

    # ✅ Optional: Chart-ready structure (if you want frontend charting)
    performance_data = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            'id', 'group_property_id', 'group_owner_name', 'title', 'address', 'location', 'city',
            'zip_code', 'description', 'status', 'property_type', 'year_bought', 'area', 'num_units',
            'initial_cost', 'current_value', 'currency', 'virtual_tour_url', 'slot_price', 'total_slots',
            'user_slots', 'available_slots', 'appreciation', 'images', 'image_files', 'documents', 'videos',
            'coordinates', 'percentage_performance', 'roi', 'incomes', 'expenses', 'owner', 'performance_data',
        ]
        read_only_fields = [
            'id', 'added_on', 'owner', 'available_slots',
            'appreciation', 'percentage_performance', 'roi'
        ]

    # === Custom Getters ===

    def get_available_slots(self, obj):
        return obj.available_slots() if obj.total_slots is not None else None

    def get_appreciation(self, obj):
        return obj.appreciation() if callable(getattr(obj, 'appreciation', None)) else None

    def get_roi(self, obj):
        return obj.roi() if callable(getattr(obj, 'roi', None)) else None

    def get_percentage_performance(self, obj):
        return obj.percentage_performance() if callable(getattr(obj, 'percentage_performance', None)) else None

    def get_group_property_id(self, obj):
        return obj.group_property.id if obj.group_property else None

    def get_group_owner_name(self, obj):
        return obj.group_property.group_owner.name if obj.group_property and obj.group_property.group_owner else None

    def get_image_files(self, obj):
        images = obj.portfolio_property_files.all()
        return PortfolioPropertyFileSerializer(
            [f for f in images if f.file_type() == 'image'], many=True
        ).data

    def get_documents(self, obj):
        docs = obj.portfolio_property_files.all()
        return PortfolioPropertyFileSerializer(
            [f for f in docs if f.file_type() in ['document', 'pdf']], many=True
        ).data

    def get_videos(self, obj):
        vids = obj.portfolio_property_files.all()
        return PortfolioPropertyFileSerializer(
            [f for f in vids if f.file_type() == 'video'], many=True
        ).data

    def get_coordinates(self, obj):
        return [
            {"id": c.id, "latitude": c.latitude, "longitude": c.longitude}
            for c in obj.coordinates.all()
        ]

    # ✅ Chart-friendly format for frontend visualization

    def get_performance_data(self, obj):
        return get_performance_data(obj)

    # def get_performance_data(self, obj):
    #     history = obj.value_history.all().order_by('recorded_at')
    #     if not history.exists():
    #         return None

    #     labels = [h.recorded_at.strftime('%Y') for h in history]
    #     data = [float(h.value) / 1_000_000 for h in history]
    #     return {
    #         "labels": labels,
    #         "datasets": [{"data": data}],
    #         "unit": "Million",
    #     } if history else None


class PortfolioSummarySerializer(serializers.Serializer):
    total_initial_cost = serializers.SerializerMethodField()
    total_current_value = serializers.SerializerMethodField()
    total_income = serializers.SerializerMethodField()
    total_expenses = serializers.SerializerMethodField()
    net_cash_flow = serializers.SerializerMethodField()

    def convert_currency(self, amount, from_currency, to_currency, rates):
        if from_currency == to_currency:
            return Decimal(amount)
        base_rate = Decimal(rates.get(from_currency, 1))
        target_rate = Decimal(rates.get(to_currency, 1))
        if base_rate == 0:
            raise ValueError(f"Invalid rate for {from_currency}")
        return Decimal(amount) * target_rate / base_rate

    def aggregate_properties(self, properties):
        preferred_currency = self.context.get('currency', 'USD')
        rates = self.context.get('rates', {})
        totals = {
            "initial_cost": Decimal(0),
            "current_value": Decimal(0),
            "income": Decimal(0),
            "expenses": Decimal(0),
        }

        for prop in properties:
            totals["initial_cost"] += self.convert_currency(
                prop.initial_cost, prop.currency, preferred_currency, rates
            )
            totals["current_value"] += self.convert_currency(
                prop.current_value, prop.currency, preferred_currency, rates
            )
            for income in prop.incomes.all():
                totals["income"] += self.convert_currency(
                    income.amount, income.currency, preferred_currency, rates
                )
            for expense in prop.expenses.all():
                totals["expenses"] += self.convert_currency(
                    expense.amount, expense.currency, preferred_currency, rates
                )

        totals["net_cash_flow"] = totals["income"] - totals["expenses"]
        return totals

    def get_total_initial_cost(self, obj):
        return self.aggregate_properties(obj)["initial_cost"]

    def get_total_current_value(self, obj):
        return self.aggregate_properties(obj)["current_value"]

    def get_total_income(self, obj):
        return self.aggregate_properties(obj)["income"]

    def get_total_expenses(self, obj):
        return self.aggregate_properties(obj)["expenses"]

    def get_net_cash_flow(self, obj):
        return self.aggregate_properties(obj)["net_cash_flow"]
