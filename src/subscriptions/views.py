from .models import SubscriptionCancellation
from .serializers import SubscriptionPlanSerializer
from .models import SubscriptionPlan
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from subscriptions.models import UserSubscription, SubscriptionPlan
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from .models import SubscriptionPlan, UserSubscription
from .models import UserSubscription
from datetime import timedelta
from django.utils import timezone
import requests
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .models import SubscriptionPlan, Payment


import requests
from django.conf import settings
from .models import Payment

import requests
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import SubscriptionPlan, UserSubscription, PlanDuration
from decimal import Decimal
from accounts.models import User


def check_customer_authorization(email):
    url = f"https://api.paystack.co/customer/{email}"
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}

    response = requests.get(url, headers=headers)
    res_data = response.json()

    if res_data.get("status"):
        customer_data = res_data["data"]
        if customer_data.get("authorizations"):
            return True
    return False


def initialize_transaction(email, price, plan_code):
    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    amount_in_kobo = int(float(price) * 100)

    data = {
        "email": email,
        "amount": amount_in_kobo,
        "plan": plan_code,
    }

    response = requests.post(url, headers=headers, json=data)
    return response.json()


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_paystack_subscription(request):
    user = request.user
    plan_id = request.data.get("plan_id")

    if not plan_id:
        return Response({"error": "Plan ID is required"}, status=400)

    plan = get_object_or_404(PlanDuration, id=plan_id)

    print(plan)

    if not plan.paystack_plan_code:
        return Response({"error": "Plan is not linked to Paystack"}, status=400)

    if not user.email:
        return Response({"error": "User email is required"}, status=400)

    plan_price = float(plan.price) if isinstance(
        plan.price, Decimal) else plan.price

    if not check_customer_authorization(user.email):
        transaction_response = initialize_transaction(
            user.email, plan_price, plan.paystack_plan_code)

        if not transaction_response.get("status"):
            return Response({"error": "Failed to initialize transaction"}, status=400)

        return Response({
            "status": "redirect",
            "message": "Customer needs to authorize payment",
            "authorization_url": transaction_response["data"].get("authorization_url")
        })

    url = "https://api.paystack.co/subscription"
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
               "Content-Type": "application/json"}
    data = {"customer": user.email, "plan": plan.paystack_plan_code}

    response = requests.post(url, headers=headers, json=data)
    res_data = response.json()

    if res_data.get("status"):
        sub_data = res_data["data"]

        try:
            existing_subscription = UserSubscription.objects.filter(
                user=user).first()
            print(f"Existing Subscription: {existing_subscription}")

            subscription, created = UserSubscription.objects.update_or_create(
                user=user,
                defaults={
                    "plan": plan,
                    "subscription_code": sub_data.get("subscription_code"),
                    "email_token": sub_data.get("email_token"),
                    "status": sub_data.get("status"),
                    "next_payment_date": sub_data.get("next_payment_date"),
                },
            )
            print(f"Subscription Updated: {subscription}, Created: {created}")

        except Exception as e:
            print(f"Error updating subscription: {str(e)}")

        return Response({
            "status": "success",
            "message": "Subscription created",
            "subscription_data": sub_data
        })

    return Response({"error": res_data.get("message", "Subscription failed")}, status=400)


@csrf_exempt
def paystack_webhook(request):
    try:
        payload = json.loads(request.body)
        event = payload.get("event")

        # print(f"Received Paystack Webhook: {event}")

        if event in ["subscription.create", "subscription.charge.success"]:
            data = payload.get("data", {})
            email = data.get("customer", {}).get("email")
            plan_code = data.get("plan", {}).get("plan_code")
            subscription_code = data.get("subscription_code")
            status = data.get("status")
            next_payment_date = data.get("next_payment_date")

            if not email or not plan_code or not subscription_code:
                return JsonResponse({"error": "Missing required data"}, status=400)

            user = User.objects.filter(email=email).first()
            plan = PlanDuration.objects.filter(
                paystack_plan_code=plan_code).first()

            if not user or not plan:
                return JsonResponse({"error": "User or Plan not found"}, status=404)

            subscription, created = UserSubscription.objects.update_or_create(
                user=user,
                defaults={
                    "plan": plan,
                    "subscription_code": subscription_code,
                    "status": status,
                    "next_payment_date": next_payment_date,
                },
            )

            return JsonResponse({"message": "Subscription updated successfully"}, status=200)

        return JsonResponse({"message": "Event ignored"}, status=200)

    except Exception as e:
        print(f"Webhook Error: {str(e)}")
        return JsonResponse({"error": "Webhook processing failed"}, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cancel_paystack_subscription(request):
    user = request.user
    subscription_code = request.data.get("subscription_code")
    cancellation_reason = request.data.get("cancellationReason")

    if not subscription_code:
        return Response({"error": "Subscription code is required"}, status=400)

    try:
        subscription = UserSubscription.objects.get(
            user=user, subscription_code=subscription_code)
    except UserSubscription.DoesNotExist:
        return Response({"error": "Subscription not found"}, status=404)

    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}

    details_url = f"https://api.paystack.co/subscription/{subscription_code}"
    details_response = requests.get(details_url, headers=headers)

    if details_response.status_code != 200:
        return Response({"error": "Failed to retrieve subscription details"}, status=400)

    details_data = details_response.json()

    email_token = details_data.get("data", {}).get("email_token")

    if not email_token:
        return Response({"error": "email_token is required but missing"}, status=400)

    disable_url = "https://api.paystack.co/subscription/disable"
    disable_data = {
        "code": subscription_code,
        "token": email_token
    }

    disable_response = requests.post(
        disable_url, headers=headers, json=disable_data)
    disable_res_data = disable_response.json()

    if disable_response.status_code != 200:
        return Response({"error": disable_res_data.get("message", "Cancellation failed")}, status=400)

    free_plan_obj = SubscriptionPlan.objects.get(name="free")
    free_plan = PlanDuration.objects.filter(plan=free_plan_obj).first()

    if not free_plan:
        return Response({"error": "Free plan not found"}, status=500)

    subscription.plan = free_plan
    subscription.status = "active"
    subscription.subscription_code = None
    subscription.save()

    SubscriptionCancellation.objects.create(
        user=user,
        subscription=subscription,
        reason=cancellation_reason
    )

    return Response({"status": "success", "message": "Subscription downgraded to free plan"})


@api_view(["GET"])
@permission_classes([AllowAny])
def get_subscription_plans(request):
    plans = SubscriptionPlan.objects.prefetch_related('durations').all()
    serializer = SubscriptionPlanSerializer(plans, many=True)
    return Response(serializer.data)


