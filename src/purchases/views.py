from rest_framework.exceptions import ValidationError
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import PropertyPurchase, MarketProperty, PaymentPlan, InstallmentPayment
from .serializers import PropertyPurchaseSerializer, InstallmentPaymentSerializer, PaymentPlanSerializer
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .utils import generate_invoice


class PaymentPlanListView(APIView):
    def get(self, request):
        payment_plans = PaymentPlan.objects.all()
        serializer = PaymentPlanSerializer(payment_plans, many=True)
        return Response(serializer.data)


def send_order_confirmation_email(user, property_purchase):
    subject = "Order Created: Property Purchase"
    context = {
        "user": user,
        "property": property_purchase.property,
        "payment_plan": property_purchase.payment_plan,
        "order_id": property_purchase.id,
        "amount": property_purchase.total_amount,
        "monthly_installment": property_purchase.monthly_installment,
        "contact_email": "sales@realvistaproperties.com",
        "due_date": "7 days from now"
    }

    invoice_path = generate_invoice(property_purchase)

    html_message = render_to_string("emails/order_confirmation.html", context)
    plain_message = strip_tags(html_message)
    from_email = "Realvista <noreply@realvistaproperties.com>"

    user_email = [user.email]
    email = EmailMultiAlternatives(
        subject, plain_message, from_email, user_email)
    email.attach_alternative(html_message, "text/html")

    with open(invoice_path, "rb") as pdf_file:
        email.attach(f"Invoice_{property_purchase.id}.pdf",
                     pdf_file.read(), "application/pdf")

    email.send()

    sales_subject = f"New Order Created by {user.name}"
    sales_message = (
        f"User: {user.name} ({user.email})\n"
        f"Property: {property_purchase.property}\n"
        f"Payment Plan: {property_purchase.payment_plan}\n"
        f"Order ID: {property_purchase.id}\n"
        f"Total Amount: {property_purchase.currency} {property_purchase.total_amount}\n"
        f"Status: Created\n"
    )

    sales_email = ["sales@realvistaproperties.com"]
    sales_notification = EmailMultiAlternatives(
        sales_subject, sales_message, from_email, sales_email)
    sales_notification.send()


class CreatePropertyPurchaseView(generics.CreateAPIView):
    serializer_class = PropertyPurchaseSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        property_id = request.data.get('property')
        payment_plan_id = request.data.get('payment_plan')

        try:
            property_instance = MarketProperty.objects.get(id=property_id)
            payment_plan_instance = PaymentPlan.objects.get(id=payment_plan_id)
        except MarketProperty.DoesNotExist:
            return Response({'error': 'Property not found'}, status=status.HTTP_404_NOT_FOUND)
        except PaymentPlan.DoesNotExist:
            return Response({'error': 'Payment plan not found'}, status=status.HTTP_404_NOT_FOUND)

        property_purchase = PropertyPurchase.objects.create(
            user=user,
            property=property_instance,
            payment_plan=payment_plan_instance,
            status='created',
            currency=property_instance.currency
        )

        send_order_confirmation_email(user, property_purchase)

        serializer = self.get_serializer(property_purchase)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


def send_cancellation_email(user_email, user_name, order_id, currency, refund_amount):
    subject = "Order Cancellation Notice"

    context = {
        "user_name": user_name,
        "order_id": order_id,
        "currency": currency,
        "refund_amount": refund_amount
    }
    html_content = render_to_string("emails/order_cancellation.html", context)
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject, text_content, "Realvista <noreply@realvistaproperties.com>", [
            user_email]
    )
    email.attach_alternative(html_content, "text/html")
    email.send()

    sales_subject = f"Order Cancellation - {user_name}"
    sales_message = f"""
    Order ID: {order_id} has been canceled by {user_name}.
    Refund Amount: {currency} {refund_amount}
    
    Please take necessary actions.
    """
    send_mail(sales_subject, sales_message,
              "Realvista <noreply@realvistaproperties.com>",
              ["sales@realvistaproperties.com"])


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_order(request, order_id):
    try:
        order = PropertyPurchase.objects.get(id=order_id, user=request.user)
    except PropertyPurchase.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

    try:
        refund_amount = order.cancel_order()

        send_cancellation_email(
            request.user.email, request.user.name, order.id, order.currency, refund_amount)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        "message": "Order has been canceled.",
        "refund_amount": str(refund_amount)
    }, status=status.HTTP_200_OK)


class InstallmentPaymentCreateView(generics.CreateAPIView):
    queryset = InstallmentPayment.objects.all()
    serializer_class = InstallmentPaymentSerializer

    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
            payment = self.get_queryset().get(id=response.data["id"])

            user_email = payment.purchase.user.email
            admin_email = "sales@realvistaproperties.com"

            subject = "Payment Confirmation"
            context = {
                "user_name": payment.purchase.user.name,
                "property_name": payment.purchase.property.title,
                "amount": payment.amount,
                "currency": payment.purchase.currency,
                "remaining_balance": payment.purchase.remaining_balance(),
                "timestamp": payment.timestamp,
            }

            email_html = render_to_string(
                "emails/payment_confirmation.html", context)
            email_plain = strip_tags(email_html)

            send_mail(
                subject,
                email_plain,
                "Realvista <noreply@realvistaproperties.com>",
                [user_email],
                html_message=email_html,
            )

            send_mail(
                "New Payment Received",
                f"A new payment of {payment.purchase.currency} {payment.amount} has been received from {payment.purchase.user.name} "
                f"for the property: {payment.purchase.property.title}.",
                "Realvista <noreply@realvistaproperties.com>",
                [admin_email],
            )

            return response

        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
