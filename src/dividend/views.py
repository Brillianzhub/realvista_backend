from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from .models import Dividend, DividendShare
from projects.models import Project
from order.models import Order

from .serializers import DividendSerializer


class CreateDividendAPIView(APIView):
    """
    API View to handle the creation of a dividend and its associated shares.
    """

    def post(self, request, *args, **kwargs):
        data = request.data
        project_id = data.get("project_id")
        total_return = data.get("total_return")
        total_expenses = data.get("total_expenses")
        retention_percentage = data.get(
            "retention_percentage", 1.00)  # Default to 1%

        # Validate input data
        if not project_id or not total_return or not total_expenses:
            return Response(
                {"error": "project_id, total_return, and total_expenses are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {"error": "Project not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            total_return = float(total_return)
            total_expenses = float(total_expenses)
            net_return = total_return - total_expenses

            if net_return < 0:
                return Response(
                    {"error": "Net return cannot be negative."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValueError:
            return Response(
                {"error": "total_return and total_expenses must be valid numbers."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            # Create the dividend entry
            dividend = Dividend.objects.create(
                project=project,
                total_return=total_return,
                total_expenses=total_expenses
            )

            # Calculate and create DividendShare entries
            orders = project.orders.all()
            total_slots = sum(order.quantity for order in orders)

            if total_slots == 0:
                return Response(
                    {"error": "No slots sold for this project. Cannot calculate shares."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            for order in orders:
                user_share = (order.quantity / total_slots) * net_return
                final_share = user_share * (1 - (retention_percentage / 100))

                DividendShare.objects.create(
                    dividend=dividend,
                    user=order.user,
                    share_amount=user_share,
                    retention_percentage=retention_percentage,
                    final_share_amount=final_share,
                    net_return=net_return,
                    total_slots=total_slots
                )

            # Serialize the created dividend for the response
            serializer = DividendSerializer(dividend)
            return Response(
                {"success": True, "dividend": serializer.data},
                status=status.HTTP_201_CREATED
            )
