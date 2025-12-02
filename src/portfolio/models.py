from datetime import datetime
from django.utils import timezone
from pyproj import Proj, transform
from django.db import models
from accounts.models import User
from shapely.geometry import Polygon
from geopy.distance import geodesic
from enterprise.models import GroupProperty
from django.db import models
from realvista_backend.currencies import CURRENCY_DATA


def upload_to(instance, filename):
    extension = filename.split('.')[-1].lower()
    now = datetime.now().strftime("%Y/%m/%d/")
    if extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
        return f'property_images/{now}{filename}'
    elif extension in ['mp4', 'mp3', 'mov', 'avi', 'mkv']:
        return f'property_videos/{now}{filename}'
    else:
        return f'property_documents/{now}{filename}'


class Property(models.Model):

    PROPERTY_TYPE_CHOICES = [
        ('house', 'House'),
        ('apartment', 'Apartment'),
        ('land', 'Land'),
        ('commercial', 'Commercial Property'),
        ('office', 'Office Space'),
        ('warehouse', 'Warehouse'),
        ('shop', 'Shop/Store'),
        ('duplex', 'Duplex'),
        ('bungalow', 'Bungalow'),
        ('terrace', 'Terrace'),
        ('semi_detached', 'Semi-Detached House'),
        ('detached', 'Detached House'),
        ('farm_land', 'Farm Land'),
        ('industrial', 'Industrial Property'),
        ('short_let', 'Short Let'),
        ('studio', 'Studio Apartment'),
    ]

    STATUS_CHOICES = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('under_maintenance', 'Under Maintenance'),
    ]

    CURRENCY_CHOICES = [(key, label) for key, label in CURRENCY_DATA.items()]

    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='properties'
    )
    group_property = models.ForeignKey(
        GroupProperty,
        on_delete=models.CASCADE,
        related_name='user_properties',
        null=True,
        blank=True,
        help_text="The group property this user property is associated with."
    )
    title = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    city = models.CharField(
        max_length=100, null=True, blank=True, help_text="City where the property is located")
    location = models.CharField(max_length=255)
    zip_code = models.CharField(
        max_length=20, null=True, blank=True, help_text="Zip code of the property location")
    description = models.TextField(blank=True, null=True)
    status = models.CharField(choices=STATUS_CHOICES, max_length=20)
    property_type = models.CharField(
        max_length=50, choices=PROPERTY_TYPE_CHOICES
    )
    year_bought = models.PositiveIntegerField(null=True, blank=True)
    area = models.FloatField(null=True, blank=True)
    num_units = models.IntegerField(default=1)
    initial_cost = models.DecimalField(max_digits=15, decimal_places=2)
    current_value = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='NGN',
        help_text="Currency for the property transactions."
    )
    slot_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True, blank=True,
        editable=False,
        help_text="Price per slot for group-owned properties."
    )
    slot_price_current = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True, blank=True,
        editable=False,
        help_text="Price per slot, calculated based on current cost and total slots."
    )
    total_slots = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Total number of slots for group-owned properties."
    )
    user_slots = models.PositiveIntegerField(
        default=0,
        help_text="Number of slots owned by the user for group-owned properties."
    )
    virtual_tour_url = models.URLField(blank=True, null=True)
    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Property"
        verbose_name_plural = "Properties"

    def __str__(self):
        return f"{self.title} posted by {self.owner}"

    def appreciation(self):
        if self.current_value is None or self.initial_cost is None:
            return None
        return self.current_value - self.initial_cost

    def available_slots(self):
        if self.total_slots is None:
            return None
        return self.total_slots - self.user_slots

    def percentage_performance(self):
        appreciation = self.appreciation()
        if appreciation is None or self.initial_cost is None or self.initial_cost == 0:
            return None
        return (appreciation / self.initial_cost) * 100

    def roi(self):
        if self.current_value is None or self.initial_cost is None or self.initial_cost == 0:
            return None
        return (self.current_value / self.initial_cost) - 1



class Income(models.Model):

    CURRENCY_CHOICES = [(key, label) for key, label in CURRENCY_DATA.items()]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_incomes",
        help_text="The user receiving the income."
    )
    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name='incomes')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='NGN',
        help_text="Currency for the property transactions."
    )
    description = models.TextField(blank=True, null=True)
    date_received = models.DateField()

    def __str__(self):
        return f'{self.amount} for {self.property.title}'


class Expenses(models.Model):

    CURRENCY_CHOICES = [(key, label) for key, label in CURRENCY_DATA.items()]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_expenses",
        help_text="The user incurring the expense."
    )
    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name='expenses')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='NGN',
        help_text="Currency for the property transactions."
    )
    description = models.TextField(blank=True, null=True)
    date_incurred = models.DateField()

    def __str__(self):
        return f'{self.amount} for {self.property.title}'


class Coordinate(models.Model):
    property = models.ForeignKey(
        'Property', on_delete=models.CASCADE, related_name='coordinates'
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    def __str__(self):
        return f"Coordinate ({self.latitude}, {self.longitude}) for {self.property}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    @staticmethod
    def convert_utm_to_wgs84(utm_x, utm_y, zone=32):
        utm_proj = Proj(proj='utm', zone=zone, ellps='WGS84')
        wgs84_proj = Proj(proj='latlong', datum='WGS84')
        longitude, latitude = transform(utm_proj, wgs84_proj, utm_x, utm_y)
        return latitude, longitude

    def set_utm_coordinates(self, utm_x, utm_y):
        self._utm_x = utm_x
        self._utm_y = utm_y


class PortfolioPropertyImage(models.Model):
    property = models.ForeignKey(
        Property,
        related_name='portfolio_property_images',
        on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to=upload_to, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class PortfolioPropertyFile(models.Model):
    property = models.ForeignKey(
        Property,
        related_name='portfolio_property_files',
        on_delete=models.CASCADE
    )
    file = models.FileField(upload_to=upload_to, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def file_type(self):
        if self.file:
            ext = self.file.name.split('.')[-1].lower()
            if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
                return 'image'
            elif ext in ['pdf']:
                return 'pdf'
            elif ext in ['doc', 'docx']:
                return 'document'
            elif ext in ['mp4', 'mp3', 'mov', 'avi', 'mkv']:
                return 'video'
        return 'unknown'

    def __str__(self):
        return f'{self.property.title} - {self.name or self.file.name}'


class CurrencyRate(models.Model):
    currency_code = models.CharField(max_length=3, unique=True)
    rate = models.DecimalField(max_digits=20, decimal_places=6)
    description = models.CharField(max_length=255, blank=True, null=True)
    base = models.CharField(max_length=3, blank=True, null=True)

    def __str__(self):
        return f"{self.currency_code}: {self.rate} (Base: {self.base})"


class PropertyValueHistory(models.Model):
    property = models.ForeignKey(
        'Property',
        on_delete=models.CASCADE,
        related_name='value_history'
    )
    value = models.DecimalField(max_digits=15, decimal_places=2)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['recorded_at']

    def __str__(self):
        return f"{self.property.title} - {self.value} on {self.recorded_at.date()}"
