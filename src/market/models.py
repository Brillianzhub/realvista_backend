from pyproj import Proj, transform
from datetime import datetime
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from accounts.models import User
from realvista_backend.currencies import CURRENCY_DATA


class MarketProperty(models.Model):
    PROPERTY_TYPES = [
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

    AVAILABILITY_CHOICES = [
        ('now', 'Available Now'),
        ('date', 'Available from Specified Date'),
    ]

    LISTING_PURPOSE_CHOICES = [
        ('sale', 'For Sale'),
        ('lease', 'For Lease'),
        ('rent', 'For Rent'),
    ]

    CATEGORY_CHOICES = [
        ('corporate', 'Corporate'),
        ('p2p', 'Peer-to-Peer'),
    ]

    CURRENCY_CHOICES = [(key, label) for key, label in CURRENCY_DATA.items()]

    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='market_properties')
    title = models.CharField(
        max_length=255, help_text="Title of the property listing")
    description = models.TextField(
        help_text="Detailed description of the property")
    property_type = models.CharField(
        max_length=50, choices=PROPERTY_TYPES, help_text="Type of property")
    price = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="Price of the property")
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='NGN',
        help_text="Currency for the property transactions."
    )
    listing_purpose = models.CharField(
        max_length=10,
        choices=LISTING_PURPOSE_CHOICES,
        default='sale',
    )

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='corporate',
        help_text="Listing category: Corporate or Peer-to-Peer."
    )
    address = models.TextField(help_text="Address of the property")
    city = models.CharField(
        max_length=100, help_text="City where the property is located")
    state = models.CharField(
        max_length=100, help_text="State where the property is located")
    zip_code = models.CharField(
        max_length=20, null=True, blank=True, help_text="Zip code of the property location")
    availability = models.CharField(
        max_length=10,
        choices=AVAILABILITY_CHOICES,
        default='now',
    )
    availability_date = models.DateField(
        null=True,
        blank=True,
        help_text="Specify date if 'Available from Specified Date' is selected.",
    )
    bedrooms = models.PositiveIntegerField(
        null=True, blank=True, help_text="Number of bedrooms")
    bathrooms = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True, help_text="Number of bathrooms (e.g., 1.5)")
    square_feet = models.PositiveIntegerField(
        null=True, blank=True, help_text="Square meter of the property")
    lot_size = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, help_text="Plot size in square meter")
    year_built = models.PositiveIntegerField(
        null=True, blank=True, help_text="Year the property was built")
    views = models.PositiveIntegerField(
        default=0,
        null=True,
        blank=True,
        help_text="Number of times the property has been viewed."
    )
    inquiries = models.PositiveIntegerField(
        default=0,
        null=True,
        blank=True,
        help_text="Number of times the user has been contacted for the property."
    )
    bookmarked = models.PositiveIntegerField(
        default=0,
        null=True,
        blank=True,
        help_text="Number of times the property has been bookmarked."
    )
    listed_date = models.DateTimeField(
        auto_now_add=True, help_text="Date when the property was listed")
    updated_date = models.DateTimeField(
        auto_now=True, help_text="Date when the property details were last updated")
    coordinate_url = models.URLField(blank=True, null=True)
    payment_plans = models.ManyToManyField(
        'purchases.PaymentPlan', related_name='properties', blank=True)

    def clean(self):
        if self.property_type == 'land' and (self.bedrooms or self.bathrooms):
            raise ValidationError({
                'bedrooms': "Land cannot have bedrooms.",
                'bathrooms': "Land cannot have bathrooms."
            })

    def __str__(self):
        return f"{self.title} - {self.city}, {self.state}"

    class Meta:
        verbose_name = "MarketProperty"
        verbose_name_plural = "MarketProperties"
        ordering = ['-listed_date']


class BookmarkedProperty(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="bookmarks")
    property = models.ForeignKey(
        'MarketProperty', on_delete=models.CASCADE, related_name="bookmarked_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'property')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} bookmarked {self.property.title}"


def upload_to(instance, filename):
    now = datetime.now().strftime("%Y/%m/%d/")
    return f"property_images/{now}{filename}"


class PropertyImage(models.Model):
    property = models.ForeignKey(
        MarketProperty,
        related_name='images',
        on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to=upload_to, null=True, blank=True)
    image_url = models.URLField(max_length=500, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if not self.image and not self.image_url:
            raise ValidationError(
                "Either an image file or an image URL must be provided.")
        if self.image and self.image_url:
            raise ValidationError(
                "Only one of `image` or `image_url` can be set.")


class MarketPropertyFile(models.Model):
    property = models.ForeignKey(
        MarketProperty,
        related_name='market_property_files',
        on_delete=models.CASCADE
    )
    file = models.FileField(upload_to=upload_to, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    image_url = models.URLField(max_length=500, null=True, blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if not self.file and not self.image_url:
            raise ValidationError(
                "Either an image file or an image URL must be provided.")
        if self.file and self.image_url:
            raise ValidationError(
                "Only one of `file` or `image_url` can be set.")

        if self.file:
            ext = self.file.name.split('.')[-1].lower()
            allowed_exts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'heic', 'heif']
            if ext not in allowed_exts:
                raise ValidationError(f"Unsupported file format: .{ext}")

    def file_type(self):
        if self.file:
            ext = self.file.name.split('.')[-1].lower()
            if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'heic', 'heif']:
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


class MarketFeatures(models.Model):
    NEGOTIABILITY_CHOICES = [
        ('yes', 'Yes'),
        ('slightly', 'Slightly'),
        ('no', 'No'),
    ]

    ELECTRICITY_PROXIMITY_CHOICES = [
        ('nearby', 'Nearby (Less than 100m)'),
        ('moderate', 'Moderate (100m - 500m)'),
        ('far', 'Far (Above 500m)'),
        ('available', 'Available'),
    ]

    ROAD_NETWORK_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ]

    DEVELOPMENT_LEVEL_CHOICES = [
        ('high', 'Highly Developed'),
        ('moderate', 'Moderately Developed'),
        ('low', 'Sparsely Developed'),
        ('undeveloped', 'Undeveloped'),
    ]

    market_property = models.ForeignKey(
        MarketProperty,
        on_delete=models.CASCADE,
        related_name='features',
        help_text="The market property this feature is associated with."
    )
    negotiable = models.CharField(
        max_length=10,
        choices=NEGOTIABILITY_CHOICES,
        default='no',
        help_text="Is the property price negotiable?"
    )
    furnished = models.BooleanField(
        default=False,
        help_text="Is the property furnished?"
    )
    pet_friendly = models.BooleanField(
        default=False,
        help_text="Is the property pet-friendly?"
    )
    parking_available = models.BooleanField(
        default=False,
        help_text="Does the property include parking space?"
    )
    swimming_pool = models.BooleanField(
        default=False,
        help_text="Does the property have a swimming pool?"
    )
    garden = models.BooleanField(
        default=False,
        help_text="Does the property include a garden?"
    )
    electricity_proximity = models.CharField(
        max_length=10,
        choices=ELECTRICITY_PROXIMITY_CHOICES,
        default='moderate',
        help_text="Proximity to electricity connection."
    )
    road_network = models.CharField(
        max_length=10,
        choices=ROAD_NETWORK_CHOICES,
        default='good',
        help_text="Quality of the road network around the property."
    )
    development_level = models.CharField(
        max_length=15,
        choices=DEVELOPMENT_LEVEL_CHOICES,
        default='moderate',
        help_text="Level of development in the surrounding area."
    )
    water_supply = models.BooleanField(
        default=False,
        help_text="Is there a reliable water supply to the property?"
    )
    security = models.BooleanField(
        default=False,
        help_text="Is the area secure?"
    )
    additional_features = models.TextField(
        blank=True,
        null=True,
        help_text="Any additional features not listed above."
    )

    verified_user = models.BooleanField(
        default=False,
        help_text="Automatically marked true if the property owner is verified."
    )

    def save(self, *args, **kwargs):

        self.verified_user = self.market_property.owner.is_identity_verified
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Features for {self.market_property.title}"


class MarketCoordinate(models.Model):
    property = models.ForeignKey(
        'MarketProperty', on_delete=models.CASCADE, related_name='market_coordinates'
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
