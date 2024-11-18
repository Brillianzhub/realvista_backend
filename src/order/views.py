# Assume you have these utilities
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Order
from accounts.models import User
from django.shortcuts import get_object_or_404, render

from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from rest_framework.decorators import api_view
from rest_framework.response import Response
from realvista_backend.utility import send_invoice_email


@csrf_exempt
def send_email_view(request):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            user_email = payload.get('user_email')
            user_name = payload.get('user_name')
            project_name = payload.get('project_name')
            total_amount = payload.get('total_amount')

            if not user_email or not user_name or not project_name or not total_amount:
                return JsonResponse({'error': 'Missing required fields'}, status=400)

            send_invoice_email(user_email, project_name,
                               total_amount, user_name)

            return JsonResponse({'message': 'Invoice email sent successfully!'})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)


@api_view(['POST'])
def create_order_view(request):
    try:
        user_id = request.data.get('user_id')
        project_name = request.data.get('project_name')
        quantity = int(request.data.get('quantity', 1))
        total_amount = float(request.data.get('total_amount'))

        user = User.objects.get(id=user_id)

        # Create and save the order
        order = Order.objects.create(
            user=user,
            project_name=project_name,
            quantity=quantity,
            total_amount=total_amount
        )

        return Response(
            {
                "success": True,
                "message": "Order created successfully!",
                "order_reference": order.order_reference,
                "order_details": {
                    "id": order.id,
                    "project_name": order.project_name,
                    "quantity": order.quantity,
                    "total_amount": order.total_amount,
                    "payment_status": order.payment_status,
                    "created_at": order.created_at,
                },
            },
            status=status.HTTP_201_CREATED
        )
    except User.DoesNotExist:
        return Response(
            {"success": False, "message": "User does not exist."},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {"success": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def create_order_and_send_email_view(request):
    try:
        user_id = request.data.get('user_id')
        project_name = request.data.get('project_name')
        quantity = int(request.data.get('quantity', 1))
        total_amount = float(request.data.get('total_amount'))

        user = User.objects.get(id=user_id)

        order = Order.objects.create(
            user=user,
            project_name=project_name,
            quantity=quantity,
            total_amount=total_amount
        )

        email_sent = send_invoice_email(
            user_email=user.email,
            project_name=project_name,
            total_amount=total_amount,
            name=user.name(),
        )

        return Response(
            {
                "success": True,
                "message": "Order created and email sent successfully!",
                "order_reference": order.order_reference,
                "email_status": "Sent" if email_sent else "Failed",
                "order_details": {
                    "id": order.id,
                    "project_name": order.project_name,
                    "quantity": order.quantity,
                    "total_amount": order.total_amount,
                    "payment_status": order.payment_status,
                    "created_at": order.created_at,
                },
            },
            status=status.HTTP_201_CREATED
        )
    except User.DoesNotExist:
        return Response(
            {"success": False, "message": "User does not exist."},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {"success": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
