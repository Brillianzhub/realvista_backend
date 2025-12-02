from .models import GroupSlotAllocation
from django.db.models import F
from django.db.models import Sum
from django.db.models.signals import post_save
from django.db.models.signals import pre_save
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import GroupSlotAllocation, GroupIncome, GroupExpenses, GroupProperty
from decimal import Decimal
from portfolio.models import Property, Income, Expenses


@receiver(pre_save, sender=GroupSlotAllocation)
def create_or_update_user_property_on_booking(sender, instance, **kwargs):
    # Check if it's an update to the 'booked' status
    if instance.pk:
        previous = GroupSlotAllocation.objects.get(pk=instance.pk)
        if previous.status != 'booked' and instance.status == 'booked':
            # Calculate user's financial contribution
            user_initial_cost = Decimal(
                instance.slots_owned) * instance.property.slot_price
            user_current_value = Decimal(
                instance.slots_owned) * instance.property.slot_price_current

            # Create or update the user's property instance
            user_property, created = Property.objects.get_or_create(
                owner=instance.user,
                title=instance.property.title,
                defaults={
                    'group_property': instance.property,
                    'address': instance.property.address,
                    'location': instance.property.location,
                    'description': instance.property.description,
                    'status': instance.property.status,
                    'year_bought': instance.property.year_bought,
                    'area': instance.property.area,
                    'num_units': instance.property.num_units,
                    'initial_cost': user_initial_cost,
                    'current_value': user_current_value,
                    'currency': instance.property.currency,
                    'slot_price': instance.property.slot_price,
                    'slot_price_current': instance.property.slot_price_current,
                    'total_slots': instance.property.total_slots,
                    'user_slots': instance.slots_owned,
                    'virtual_tour_url': instance.property.virtual_tour_url,
                    'property_type': instance.property.property_type,
                }
            )

            # Update values if the property already exists
            if not created:
                user_property.initial_cost += user_initial_cost
                user_property.current_value += user_current_value
                user_property.user_slots += instance.slots_owned

            user_property.save()


@receiver(post_save, sender=GroupSlotAllocation)
def create_or_update_user_property_on_transfer(sender, instance, created, **kwargs):
    """
    Signal to create or update the user's property instance when slots are transferred.
    """
    if not created and instance.status == 'booked':
        if hasattr(instance, '_is_transfer') and instance._is_transfer:
            target_user = instance._target_user

            user_initial_cost = Decimal(
                instance.slots_owned) * instance.property.slot_price
            user_current_value = Decimal(
                instance.slots_owned) * instance.property.slot_price_current

            user_property, created = Property.objects.get_or_create(
                owner=target_user,
                title=instance.property.title,
                defaults={
                    'group_property': instance.property,
                    'address': instance.property.address,
                    'location': instance.property.location,
                    'description': instance.property.description,
                    'status': instance.property.status,
                    'year_bought': instance.property.year_bought,
                    'area': instance.property.area,
                    'num_units': instance.property.num_units,
                    'initial_cost': user_initial_cost,
                    'current_value': user_current_value,
                    'currency': instance.property.currency,
                    'slot_price': instance.property.slot_price,
                    'slot_price_current': instance.property.slot_price_current,
                    'total_slots': instance.property.total_slots,
                    'user_slots': instance.slots_owned,
                    'virtual_tour_url': instance.property.virtual_tour_url,
                    'property_type': instance.property.property_type,
                }
            )

            # Update values if the property already exists
            if not created:
                user_property.initial_cost += user_initial_cost
                user_property.current_value += user_current_value
                user_property.user_slots += instance.slots_owned

            user_property.save()


@receiver(post_save, sender=GroupProperty)
def update_user_properties_on_slot_price_change(sender, instance, **kwargs):

    user_properties = Property.objects.filter(group_property=instance)

    for user_property in user_properties:
        new_current_value = Decimal(
            user_property.user_slots) * instance.slot_price_current

        user_property.slot_price_current = instance.slot_price_current
        user_property.current_value = new_current_value
        user_property.save()


@receiver(post_save, sender=GroupSlotAllocation)
def update_user_property_on_cancellation(sender, instance, **kwargs):
    if instance.status == 'cancelled':
        try:
            user_property = Property.objects.get(
                owner=instance.user, title=instance.property.title
            )
            user_property.user_slots -= instance.slots_owned
            if user_property.user_slots <= 0:
                user_property.delete()
            else:
                user_property.save()
        except Property.DoesNotExist:
            pass

        group_property = instance.property
        group_property.save()


@receiver(post_save, sender=GroupIncome)
def distribute_income_to_users(sender, instance, created, **kwargs):
    if created:
        total_slots = instance.property.total_slots
        if total_slots == 0:  # Avoid division by zero
            return

        allocations = instance.property.slot_allocations.all()
        for allocation in allocations:
            user_property = Property.objects.filter(
                owner=allocation.user,
                group_property=instance.property
            ).first()

            if user_property:
                user_share = (Decimal(allocation.slots_owned) /
                              Decimal(total_slots)) * instance.amount

                Income.objects.create(
                    user=allocation.user,
                    property=user_property,
                    amount=user_share,
                    description=instance.description,
                    date_received=instance.date_received,
                )


@receiver(post_save, sender=GroupExpenses)
def distribute_expense_to_users(sender, instance, created, **kwargs):
    if created:
        total_slots = instance.property.total_slots
        if total_slots == 0:  # Avoid division by zero
            return

        allocations = instance.property.slot_allocations.all()
        for allocation in allocations:
            # Retrieve the corresponding Property instance for the user
            user_property = Property.objects.filter(
                owner=allocation.user,
                group_property=instance.property
            ).first()

            if user_property:
                # Calculate the user's share of the expense
                user_share = (Decimal(allocation.slots_owned) /
                              Decimal(total_slots)) * instance.amount

                # Create the Expenses instance for the user
                Expenses.objects.create(
                    user=allocation.user,
                    property=user_property,
                    amount=user_share,
                    description=instance.description,
                    date_incurred=instance.date_incurred,
                )
