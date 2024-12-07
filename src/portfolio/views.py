from django.shortcuts import render

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from .models import Property
from rest_framework.permissions import IsAuthenticated
from .serializers import PropertySerializer

import logging


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def add_property(request):
#     user = request.user

#     property_data = request.data.copy()
#     property_data['owner'] = user.id

#     serializer = PropertySerializer(data=property_data)
#     if serializer.is_valid():
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_property(request):
    user = request.user

    property_data = request.data.copy()
    property_data['owner'] = user.id

    serializer = PropertySerializer(data=property_data)

    # logger = logging.getLogger(__name__)
    # logger.error("Property creation failed: %s", serializer.errors)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
