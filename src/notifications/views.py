from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Device
import firebase_admin
from firebase_admin import messaging
import json
import requests
import logging

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


@csrf_exempt
def register_token(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        token = body.get('token')

        if token:
            Device.objects.get_or_create(token=token)
            return JsonResponse({'status': 'Token registered successfully'}, status=200)
        else:
            return JsonResponse({'error': 'No token provided'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_exempt
def delete_token(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        token = body.get('token')

        if token:
            try:
                # Find and delete the device entry with the given token
                device = Device.objects.get(token=token)
                device.delete()
                return JsonResponse({'status': 'Token deleted successfully'}, status=200)
            except Device.DoesNotExist:
                return JsonResponse({'error': 'Token not found'}, status=404)
        else:
            return JsonResponse({'error': 'No token provided'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)
