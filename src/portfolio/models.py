from django.contrib.auth.models import AbstractUser
from django.db import models
from accounts.models import User
from shapely.geometry import Polygon
from geopy.distance import geodesic


class Property(models.Model):

    PROPERTY_TYPE_CHOICES = [
        ('land', 'Land'),
        ('building', 'Building'),
        ('commercial', 'Commercial Property'),
        ('residential', 'Residential Property'),
    ]

    STATUS_CHOICES = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('under_maintenance', 'Under Maintenance'),
    ]

    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='properties')
    address = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(choices=STATUS_CHOICES, max_length=20)
    property_type = models.CharField(
        max_length=50, choices=PROPERTY_TYPE_CHOICES)
    num_units = models.IntegerField()
    initial_cost = models.DecimalField(max_digits=15, decimal_places=2)
    current_value = models.DecimalField(max_digits=15, decimal_places=2)
    rental_income = models.DecimalField(max_digits=10, decimal_places=2)
    expenses = models.DecimalField(max_digits=10, decimal_places=2)
    photos = models.ImageField(
        upload_to='property_photos/', blank=True, null=True)
    virtual_tour_url = models.URLField(blank=True, null=True)
    area_sqm = models.FloatField(null=True, blank=True)
    added_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_property_type_display()} at {self.location}"

    def appreciation(self):
        return self.current_value - self.initial_cost

    def calculate_area(self):
        """Calculates area based on property's coordinates and saves it in `area_sqm`."""
        coords = [(coord.latitude, coord.longitude)
                  for coord in self.coordinates.all()]
        if len(coords) < 3:
            return 0

        # Convert to meters using geodesic distances
        poly_points = []
        for i in range(len(coords)):
            point1 = coords[i]
            point2 = coords[(i + 1) % len(coords)]
            distance = geodesic(point1, point2).meters
            poly_points.append(distance)

        polygon = Polygon(poly_points)
        self.area_sqm = polygon.area
        self.save()


class Coordinate(models.Model):
    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name='coordinates')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    def __str__(self):
        return f"Coordinate ({self.latitude}, {self.longitude}) for {self.property}"
