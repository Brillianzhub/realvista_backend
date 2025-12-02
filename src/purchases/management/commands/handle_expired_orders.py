from django.core.management.base import BaseCommand
from purchases.models import PropertyPurchase


class Command(BaseCommand):
    help = "Sends reminders for expiring orders and cancels overdue orders."

    def handle(self, *args, **kwargs):
        reminder_result = PropertyPurchase.send_reminder_emails()
        cancel_result = PropertyPurchase.cancel_expired_orders()
        self.stdout.write(self.style.SUCCESS(reminder_result))
        self.stdout.write(self.style.SUCCESS(cancel_result))
