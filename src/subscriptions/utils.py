from django.conf import settings

PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY


def charge_user_for_subscription(user, amount):
    payment_success = True
    return payment_success
