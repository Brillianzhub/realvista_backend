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


@csrf_exempt
def send_notification(request):
    if request.method == 'POST':
        try:
            # Extract title and message from the request
            data = json.loads(request.body)
            title = data.get('title')
            message = data.get('message')

            if not title or not message:
                return JsonResponse({"error": "Title and message are required"}, status=400)

            # Retrieve all device tokens from the database
            devices = Device.objects.all()
            if not devices.exists():
                return JsonResponse({"error": "No device tokens found"}, status=404)

            responses = []

            # Send push notification to each device
            for device in devices:
                expo_push_token = device.token
                response = send_push_notification(
                    expo_push_token, title, message)
                responses.append(response)

            return JsonResponse({"status": "Notifications sent", "responses": responses}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)


# def send_push_notification(expo_push_token, title, message):
#     headers = {
#         'Accept': 'application/json',
#         'Content-Type': 'application/json',
#     }
#     payload = {
#         'to': expo_push_token,
#         'sound': 'default',
#         'title': title,
#         'body': message,
#     }
#     response = requests.post(EXPO_PUSH_URL, headers=headers, json=payload)
#     response_data = response.json()

#     if response_data.get('data', {}).get('status') == 'error':
#         error = response_data.get('data', {}).get('details', {}).get('error')
#         if error == 'DeviceNotRegistered':
#             Device.objects.filter(token=expo_push_token).delete()
#             print(f'Token {expo_push_token} removed from database')

#     return response_data

@csrf_exempt
def send_test_notification(request):
    try:
        # Direct string assignment for testing
        expo_push_token = "ExponentPushToken[d__EqwLyDzcvJbIOZPaMfr]"

        title = "Test Notification"
        message = "This is a test notification sent from Django backend."

        # Send push notification
        response = send_push_notification(expo_push_token, title, message)
        return JsonResponse(response, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def send_push_notification(expo_push_token, title, message):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    payload = {
        'to': expo_push_token,
        'sound': 'default',
        'title': title,
        'body': message,
    }
    response = requests.post(EXPO_PUSH_URL, headers=headers, json=payload)
    response_data = response.json()

    if response_data.get('data', {}).get('status') == 'error':
        error = response_data.get('data', {}).get('details', {}).get('error')
        if error == 'DeviceNotRegistered':
            # Assuming you have some logic to remove the token from the database
            # Device.objects.filter(token=expo_push_token).delete()
            print(f'Token {expo_push_token} removed from database')

    return response_data
