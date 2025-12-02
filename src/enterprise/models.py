from datetime import datetime, timedelta
from accounts.models import User
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.db import models, transaction
from realvista_backend.currencies import CURRENCY_DATA
from django.utils import timezone
import random
import string
from pyproj import Proj, transform


def generate_booking_reference():
    prefix = "RV"
    random_string = ''.join(random.choices(
        string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}-{random_string}-{int(timezone.now().timestamp())}"


class CorporateEntity(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    group_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text="Unique identifier for the corporate group."
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_entities",
        help_text="The user who created this entity.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class CorporateEntityMember(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('SUPERADMIN', 'SuperAdmin'),
        ('MEMBER', 'Member'),
    ]

    corporate_entity = models.ForeignKey(
        CorporateEntity,
        on_delete=models.CASCADE,
        related_name="members",
        help_text="The corporate entity this membership belongs to.",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="corporate_memberships",
        help_text="The user who is a member of this corporate entity.",
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='MEMBER',
        help_text="The role of the member in the corporate entity.",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('corporate_entity', 'user')
        verbose_name = "Corporate Entity Member"
        verbose_name_plural = "Corporate Entity Members"

    def __str__(self):
        return f"{self.user.email} - {self.corporate_entity.name} ({self.role})"


class GroupProperty(models.Model):
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

    group_owner = models.ForeignKey(
        CorporateEntity,
        on_delete=models.CASCADE,
        related_name="group_properties",
        help_text="The group that owns this property."
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
        null=True, blank=True,
        max_digits=10,
        decimal_places=2,
        # editable=False,
        help_text="Price per slot, calculated based on initial cost and total slots."
    )
    slot_price_current = models.DecimalField(
        null=True, blank=True,
        max_digits=10,
        decimal_places=2,
        editable=False,
        help_text="Price per slot, calculated based on current cost and total slots."
    )
    total_slots = models.PositiveIntegerField(
        default=100,
        help_text="Total number of slots available for this property."
    )
    virtual_tour_url = models.URLField(blank=True, null=True)
    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Group Property"
        verbose_name_plural = "Group Properties"

    def __str__(self):
        return f"{self.title}"

    def appreciation(self):
        if self.current_value is None or self.initial_cost is None:
            return None
        return self.current_value - self.initial_cost

    def available_slots(self):
        allocated_slots = self.slot_allocations.filter(
            status__in=['booked', 'pending']
        ).aggregate(
            total=models.Sum('slots_owned')
        )['total'] or 0
        return max(0, self.total_slots - allocated_slots)


class GroupCoordinate(models.Model):
    property = models.ForeignKey(
        GroupProperty, on_delete=models.CASCADE, related_name='group_coordinates'
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


class GroupIncome(models.Model):

    CURRENCY_CHOICES = [(key, label) for key, label in CURRENCY_DATA.items()]

    property = models.ForeignKey(
        GroupProperty,
        on_delete=models.CASCADE,
        related_name='incomes',
        help_text="The group property this income is associated with."
    )
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
        return f"{self.amount} for {self.property.title}"


class GroupExpenses(models.Model):

    CURRENCY_CHOICES = [(key, label) for key, label in CURRENCY_DATA.items()]

    property = models.ForeignKey(
        GroupProperty,
        on_delete=models.CASCADE,
        related_name='expenses',
        help_text="The group property this expense is associated with."
    )
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
        return f"{self.amount} for {self.property.title}"


class GroupSlotAllocation(models.Model):
    STATUS_CHOICES = [
        ('booked', 'Booked'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
    ]

    property = models.ForeignKey(
        GroupProperty,
        on_delete=models.CASCADE,
        related_name='slot_allocations',
        help_text="The group property associated with this allocation."
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='group_slot_allocations',
        help_text="The user owning these slots."
    )
    status = models.CharField(
        choices=STATUS_CHOICES,
        max_length=20,
        default='pending',
        help_text="The status of the slot allocation."
    )
    slots_owned = models.PositiveIntegerField(
        default=1,
        help_text="Number of slots owned by this user."
    )
    booking_reference = models.CharField(
        max_length=50, null=True, blank=True, unique=True, editable=False)
    total_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} owns {self.slots_owned} slots of {self.property.title}"

    def clean(self):
        self.total_cost = self.slots_owned * self.property.slot_price

        available_slots = self.property.available_slots()

        if self.pk:
            existing = GroupSlotAllocation.objects.get(pk=self.pk)
            if existing.status == 'pending':
                available_slots += existing.slots_owned

            if existing.status == 'pending' and self.status == 'booked':
                if self.slots_owned > available_slots:
                    raise ValidationError(
                        f"Not enough slots available. Only {available_slots} slots are left."
                    )
        else:
            if self.slots_owned > available_slots:
                raise ValidationError(
                    f"Not enough slots available. Only {available_slots} slots are left."
                )

    def save(self, *args, **kwargs):
        if not self.booking_reference:
            self.booking_reference = generate_booking_reference()
        self.full_clean()
        with transaction.atomic():
            super().save(*args, **kwargs)

    @classmethod
    def total_slots_owned_by_user(cls, user):
        return cls.objects.filter(user=user).aggregate(
            total=Sum('slots_owned')
        )['total'] or 0

    def transfer_slots(self, target_user, slots_to_transfer):

        if self.status != 'booked':
            raise ValidationError(
                "Only slots with status 'booked' can be transferred.")

        if self.user == target_user:
            raise ValidationError("Cannot transfer slots to the same user.")

        with transaction.atomic():
            self.slots_owned -= slots_to_transfer
            self.save()

            target_allocation, created = GroupSlotAllocation.objects.get_or_create(
                property=self.property,
                user=target_user,
                defaults={
                    'status': 'booked',
                    'slots_owned': slots_to_transfer,
                }
            )

            if not created:
                target_allocation.slots_owned += slots_to_transfer
                target_allocation.save()

            return target_allocation


class Payment(models.Model):
    booking = models.ForeignKey(GroupSlotAllocation, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(
        choices=[('successful', 'Successful'), ('failed', 'Failed')], max_length=20)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Payment of {self.amount_paid} for {self.booking}"


def upload_to(instance, filename):
    extension = filename.split('.')[-1].lower()
    now = datetime.now().strftime("%Y/%m/%d/")
    if extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
        return f'property_images/{now}{filename}'
    elif extension in ['mp4', 'mp3', 'mov', 'avi', 'mkv']:
        return f'property_videos/{now}{filename}'
    else:
        return f'property_documents/{now}{filename}'


class GroupPropertyImage(models.Model):
    property = models.ForeignKey(
        GroupProperty,
        related_name='group_property_images',
        on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to=upload_to, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class GroupPropertyFile(models.Model):
    property = models.ForeignKey(
        GroupProperty,
        related_name='group_property_files',
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


class InvitationToken(models.Model):
    token = models.CharField(max_length=10, unique=True)
    email = models.EmailField()
    corporate_entity = models.ForeignKey(
        CorporateEntity, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, default="MEMBER")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at


class ReleasedSlot(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="released_slots")
    property = models.ForeignKey(
        GroupProperty, on_delete=models.CASCADE, related_name="released_slots")
    group = models.ForeignKey(
        CorporateEntity, on_delete=models.CASCADE, related_name="released_slots")
    number_of_slots = models.PositiveIntegerField()
    released_at = models.DateTimeField(auto_now_add=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user} released {self.number_of_slots} slots in {self.property}"
