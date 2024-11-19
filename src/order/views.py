from .models import Order
from accounts.models import User

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from realvista_backend.utility import send_invoice_email


@csrf_exempt
def send_email_view(request):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            user_id = payload.get('user_id')
            user_email = payload.get('user_email')
            user_name = payload.get('user_name')
            project_name = payload.get('project_name')
            quantity = payload.get('quantity')
            total_amount = payload.get('total_amount')

            if not user_email or not user_name or not project_name or not total_amount:
                return JsonResponse({'error': 'Missing required fields'}, status=400)

            send_invoice_email(user_email, project_name,
                               total_amount, user_name)

            user = User.objects.get(id=user_id)

            order = Order.objects.create(
                user=user,
                project_name=project_name,
                quantity=quantity,
                total_amount=total_amount
            )

            return JsonResponse(
                {
                    "success": True,
                    "message": "Order created and email sent successfully!",
                    "order_reference": order.order_reference,
                    "email_status": "Sent",
                    "order_details": {
                        "id": order.id,
                        "project_name": order.project_name,
                        "quantity": order.quantity,
                        "total_amount": order.total_amount,
                        "payment_status": order.payment_status,
                        "created_at": order.created_at,
                    },
                })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
