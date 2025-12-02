from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from subscriptions.models import UserSubscription


class Command(BaseCommand):
    help = "Checks user subscriptions, deactivates expired ones, and sends reminders for expiring or expired subscriptions."

    def handle(self, *args, **kwargs):
        now = timezone.now()
        self.stdout.write(f"🔍 Checking subscriptions at {now}")

        active_subscriptions = UserSubscription.objects.filter(is_active=True)

        if active_subscriptions.exists():
            for sub in active_subscriptions:
                if sub.end_date and sub.end_date <= now:
                    sub.is_active = False
                    sub.save()
                    self.stdout.write(
                        f"❌ Deactivated subscription for User ID: {sub.user.id} "
                        f"(Expired on {sub.end_date})"
                    )

                    self.send_expired_subscription_email(sub.user.email)
                    self.stdout.write(
                        f"📧 Sent expired subscription reminder to User ID: {sub.user.id}"
                    )
                elif sub.end_date:
                    remaining_time = sub.end_date - now
                    remaining_minutes = remaining_time.total_seconds() / 60

                    if remaining_minutes < 5:
                        self.send_expiring_subscription_email(
                            sub.user.email, remaining_minutes)
                        self.stdout.write(
                            f"📧 Sent expiration reminder to User ID: {sub.user.id} "
                            f"(Expires in {remaining_minutes:.2f} minutes)"
                        )
                    else:
                        self.stdout.write(
                            f"🟢 Active subscription for User ID: {sub.user.id} "
                            f"(Expires in {remaining_minutes:.2f} minutes)"
                        )
                else:
                    self.stdout.write(
                        f"🟢 Active subscription for User ID: {sub.user.id} "
                        "(No expiration date)"
                    )
        else:
            self.stdout.write("✅ No active subscriptions found.")

        self.stdout.write("🔔 Subscription check completed.")

    def send_expiring_subscription_email(self, user_email, remaining_minutes):
        subject = "Your Subscription is About to Expire"
        html_message = render_to_string(
            "emails/expiring_subscription_email.html",
            {"remaining_minutes": remaining_minutes},
        )
        from_email = "Realvista <noreply@realvistaproperties.com>"
        recipient_list = [user_email]

        send_mail(
            subject,
            message=None,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )

    def send_expired_subscription_email(self, user_email):
        subject = "Your Subscription Has Expired"
        html_message = render_to_string(
            "emails/expired_subscription_email.html", {})
        from_email = "Realvista <noreply@realvistaproperties.com>"
        recipient_list = [user_email]

        send_mail(
            subject,
            message=None,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
