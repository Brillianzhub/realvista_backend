from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import BoostPackage, BoostOrder
from .serializers import BoostPackageSerializer, BoostOrderSerializer
from rest_framework.permissions import AllowAny

@api_view(["GET"])
@permission_classes([AllowAny])
def list_boost_packages(request):
    packages = BoostPackage.objects.all()
    serializer = BoostPackageSerializer(packages, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_boost_order(request):
    serializer = BoostOrderSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
