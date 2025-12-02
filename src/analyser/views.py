from rest_framework.decorators import action
from django.db import transaction
from datetime import datetime
from .models import Contribution
from rest_framework.views import APIView
from .serializers import ContributionSerializer
from .models import FinancialTarget, Contribution
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import FinancialTarget
from .serializers import FinancialTargetSerializer
from decimal import Decimal


class FinancialTargetViewSet(viewsets.ModelViewSet):
    queryset = FinancialTarget.objects.all()
    serializer_class = FinancialTargetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FinancialTarget.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['DELETE'])
    def delete_target(self, request, pk=None):
        try:
            target = FinancialTarget.objects.get(id=pk, user=request.user)
            target.delete()
            return Response({"message": "Financial target deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except FinancialTarget.DoesNotExist:
            return Response({"error": "Financial target not found"}, status=status.HTTP_404_NOT_FOUND)


class ContributionViewSet(viewsets.ModelViewSet):
    queryset = Contribution.objects.all()
    serializer_class = ContributionSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()


@api_view(['POST'])
def add_contribution(request, target_id):
    try:
        target = get_object_or_404(
            FinancialTarget, id=target_id, user=request.user)

        amount = request.data.get('amount')
        if not amount:
            return Response({"error": "Amount is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            amount = Decimal(amount)
        except ValueError:
            return Response({"error": "Invalid amount format."}, status=status.HTTP_400_BAD_REQUEST)

        if amount <= 0:
            return Response({"error": "Contribution amount must be positive."}, status=status.HTTP_400_BAD_REQUEST)

        date = request.data.get('date')
        try:
            date = datetime.strptime(date, '%Y-%m-%d').date() if date else None
        except ValueError:
            return Response({"error": "Invalid date format. Use 'YYYY-MM-DD'."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            contribution = Contribution.objects.create(
                target=target, amount=amount, date=date)

            target.save()

        return Response(
            {"message": "Contribution added successfully.",
                "contribution_id": contribution.id},
            status=status.HTTP_201_CREATED
        )
    except FinancialTarget.DoesNotExist:
        return Response({"error": "Financial target not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_contributions(request, target_id):
    try:
        target = get_object_or_404(
            FinancialTarget, id=target_id, user=request.user)
        contributions = target.contributions.all().order_by('-date')
        data = [{"amount": c.amount, "date": c.date} for c in contributions]
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
