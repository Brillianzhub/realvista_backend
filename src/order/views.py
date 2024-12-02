from rest_framework.decorators import action
from rest_framework import viewsets
from rest_framework.response import Response
from .serializers import OrderSerializer
from .models import Order
from accounts.models import User
from projects.models import Project
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from realvista_backend.utility import send_invoice_email
from holdings.models import Holding


@csrf_exempt
def send_email_view(request):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            user_id = payload.get('user_id')
            user_email = payload.get('user_email')
            user_name = payload.get('user_name')
            project_id = payload.get('project_id')
            project_name = payload.get('project_name')
            quantity = payload.get('quantity')
            cost_per_slot = payload.get('cost_per_slot')
            total_amount = payload.get('total_amount')

            if not user_email or not user_name or not project_name or not total_amount:
                return JsonResponse({'error': 'Missing required fields'}, status=400)

            send_invoice_email(user_name, user_email, project_name,
                               quantity, cost_per_slot, total_amount)

            user = User.objects.get(id=user_id)
            project = Project.objects.get(id=project_id)

            order = Order.objects.create(
                user=user,
                project=project,
                quantity=quantity,
                total_amount=total_amount
            )

            return JsonResponse(
                {
                    "success": True,
                    "message": "Order created and email sent successfully!",
                    "order_reference": order.order_reference,
                    "email_status": "Sent",
                    "project": {
                        "id": order.project.id,
                        "project_reference": order.project.project_reference,
                        "name": order.project.name,
                        "location": order.project.location,
                        "type_of_project": order.project.type_of_project,
                        "status": order.project.status,
                        "budget": float(order.project.budget),
                        "cost_per_slot": float(order.project.cost_per_slot),
                        "num_slots": order.project.num_slots,
                        "currency": order.project.currency,
                        "created_at": order.project.created_at,
                    },
                    "order_details": {
                        "id": order.id,
                        "project_name": order.project.project_name,
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


@csrf_exempt
def update_payment_status(request):
    if request.method == 'POST':
        try:
            payload = json.loads(request.body)
            order_id = payload.get('order_id')
            if not order_id:
                return JsonResponse({'error': 'Order ID is required'}, status=400)

            order = Order.objects.get(id=order_id)
            order.payment_status = 'paid'
            order.save()

            Holding.objects.create(
                user=order.user,
                project=order.project,
                slots=order.quantity,
                amount=order.total_amount
            )

            return JsonResponse({'message': 'Payment status updated succesfully'}, status=200)
        except Order.DoesNotExist:
            return JsonResponse({'error': 'Order not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)


class UserOrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    @action(detail=False, methods=['get'])
    def by_user_email(self, request):

        user_email = request.query_params.get('user_email')

        if not user_email:
            return Response({'error': 'Valid user email is required'}, status=400)

        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

        orders = Order.objects.filter(user=user)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)


class ProjectOrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    @action(detail=False, methods=['get'])
    def by_project(self, request):

        project_ref = request.query_params.get('project_id')

        if not project_ref:
            return Response({'error': 'Valid project name is required'}, status=400)

        try:
            project = Project.objects.get(project_reference=project_ref)
        except User.DoesNotExist:
            return Response({'error': 'Project with the name not found'}, status=404)

        orders = Order.objects.filter(project=project)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
