from django.core.management.base import BaseCommand
from django.utils import timezone
from subscriptions.models import UserSubscription
from decimal import Decimal
from subscriptions.utils import charge_user_for_subscription


class Command(BaseCommand):
    help = "Checks for expired subscriptions with auto-renew enabled and renews them."

    def handle(self, *args, **kwargs):
        now = timezone.now()
        expired_subscriptions = UserSubscription.objects.filter(
            end_date__lt=now,
            auto_renew=True,
            is_active=True
        )

        self.stdout.write(
            f"Found {expired_subscriptions.count()} expired subscriptions with auto-renew enabled.")

        for subscription in expired_subscriptions:
            user = subscription.user
            amount = subscription.plan.price

            payment_success = charge_user_for_subscription(user, amount)

            if payment_success:
                subscription.process_auto_renewal()
                self.stdout.write(self.style.SUCCESS(
                    f"Successfully renewed subscription for {user.email}"))
            else:
                subscription.is_active = False
                subscription.save()
                self.stdout.write(self.style.ERROR(
                    f"Failed to renew subscription for {user.email}"))
