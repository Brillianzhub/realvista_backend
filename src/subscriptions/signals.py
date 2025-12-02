from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import SubscriptionPlan, UserSubscription, PlanDuration
from accounts.models import User


@receiver(post_save, sender=User)
def assign_free_subscription(sender, instance, created, **kwargs):
    if created:
        try:
            free_plan = SubscriptionPlan.objects.get(
                name=SubscriptionPlan.FREE)
            free_duration = PlanDuration.objects.filter(
                plan=free_plan).first()  

            if not free_duration:
                print("No PlanDuration found for the free plan.")
                return

            UserSubscription.objects.create(user=instance, plan=free_duration)

        except SubscriptionPlan.DoesNotExist:
            print("Free SubscriptionPlan not found.")
