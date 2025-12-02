from django.db.models.signals import pre_save, post_save
from .models import Property, PropertyValueHistory
from django.db.models.signals import post_save
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.core.files.storage import default_storage
from django.apps import apps
from django.conf import settings


@receiver(post_delete)
def delete_media_files(sender, instance, **kwargs):
    """
    Deletes media files from S3 when any model instance containing a FileField or ImageField is deleted.
    """
    # Avoid deleting files for non-media models
    if not hasattr(instance, "_meta"):
        return

    # Loop through all fields of the model instance
    for field in instance._meta.fields:
        if field.get_internal_type() in ["FileField", "ImageField"]:
            file_field = getattr(instance, field.name)

            if file_field and file_field.name:
                try:
                    # Delete the file from S3 using Django Storages
                    default_storage.delete(file_field.name)
                    print(f"Deleted file: {file_field.name}")
                except Exception as e:
                    print(f"Error deleting {file_field.name}: {e}")


@receiver(pre_save, sender=Property)
def store_old_value(sender, instance, **kwargs):
    """Store the old current_value before saving."""
    if instance.pk:
        try:
            old_value = Property.objects.get(pk=instance.pk).current_value
            instance._old_current_value = old_value
        except Property.DoesNotExist:
            instance._old_current_value = None
    else:
        instance._old_current_value = None


@receiver(post_save, sender=Property)
def create_property_value_history(sender, instance, created, **kwargs):
    """Create PropertyValueHistory record when created or value changes."""
    if created:
        # Always create history for new properties
        PropertyValueHistory.objects.create(
            property=instance,
            value=instance.current_value
        )
    else:
        old_value = getattr(instance, "_old_current_value", None)
        if old_value is not None and old_value != instance.current_value:
            PropertyValueHistory.objects.create(
                property=instance,
                value=instance.current_value
            )
