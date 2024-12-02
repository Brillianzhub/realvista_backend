from rest_framework.decorators import action
from rest_framework import viewsets
from rest_framework.response import Response
from .serializers import HoldingSerializer
from accounts.models import User
from .models import Holding


class UserHoldingViewSet(viewsets.ModelViewSet):
    queryset = Holding.objects.all()
    serializer_class = HoldingSerializer

    @action(detail=False, methods=['get'])
    def by_user_email(self, request):

        user_email = request.query_params.get('user_email')

        if not user_email:
            return Response({'error': 'Valid user email is required'}, status=400)
        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

        holdings = Holding.objects.filter(user=user)
        serializer = HoldingSerializer(holdings, many=True)
        return Response(serializer.data)
