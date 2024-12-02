from .serializers import DividendShareSerializer
from accounts.models import User
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from .models import DividendShare
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from .models import Dividend, DividendShare
from projects.models import Project
from datetime import date
from holdings.models import Holding

from .serializers import DividendSerializer


class CreateDividendAPIView(APIView):

    def post(self, request, *args, **kwargs):
        data = request.data
        project_id = data.get("project_id")
        month = data.get('month', date.today())
        total_return = data.get("total_return")
        total_expenses = data.get("total_expenses")
        retention_percentage = data.get(
            "retention_percentage", 1.00)

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
            dividend = Dividend.objects.create(
                project=project,
                month=month,
                total_return=total_return,
                total_expenses=total_expenses
            )

            holdings = Holding.objects.filter(project=project)
            total_slots = sum(holding.slots for holding in holdings)

            total_slots = float(total_slots)

            if total_slots == 0:
                return Response(
                    {"error": "No slots sold for this project. Cannot calculate shares."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            retention_percentage = float(retention_percentage)

            for holding in holdings:
                user_share = (holding.slots / total_slots) * net_return
                final_share = user_share * (1 - (retention_percentage / 100))

                DividendShare.objects.create(
                    dividend=dividend,
                    user=holding.user,
                    share_amount=user_share,
                    retention_percentage=retention_percentage,
                    final_share_amount=final_share,
                    net_return=net_return,
                    total_slots=total_slots
                )

            serializer = DividendSerializer(dividend)
            return Response(
                {"success": True, "dividend": serializer.data},
                status=status.HTTP_201_CREATED
            )


class UserDividendsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        email = request.query_params.get('email')
        if not email:
            return Response({"error": "Email parameter is required."}, status=400)

        user = get_object_or_404(User, email=email)
        dividend_shares = DividendShare.objects.filter(user=user)

        total_dividends = sum(
            share.final_share_amount for share in dividend_shares)
        total_retention = sum(
            share.retention_amount for share in dividend_shares)

        serializer = DividendShareSerializer(dividend_shares, many=True)

        return Response({
            "dividends": serializer.data,
            "total_dividends": total_dividends,
            "total_retention": total_retention,
        })
