import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


@csrf_exempt
def send_push_notification(request):
    if request.method == "POST":
        try:
            # Parse JSON request body
            body = json.loads(request.body)
            push_token = body.get("to")
            title = body.get("title")
            message = body.get("body")
            data = body.get("data", {})

            if not push_token:
                return JsonResponse({"error": "Push token is required"}, status=400)

            # Create the notification payload
            payload = {
                "to": push_token,
                "sound": "default",
                "title": title,
                "body": message,
                "data": data,
            }

            # Send the notification to the Expo push service
            response = requests.post(EXPO_PUSH_URL, json=payload)
            response_data = response.json()

            if response.status_code == 200:
                return JsonResponse({"success": response_data}, status=200)
            else:
                return JsonResponse({"error": response_data}, status=response.status_code)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)


