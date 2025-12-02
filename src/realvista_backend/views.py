from rest_framework.decorators import api_view
from .serializers import CurrencyRateSerializer
from rest_framework import status
from rest_framework.permissions import AllowAny
from .serializers import HomePageStatsSerializer
from portfolio.models import CurrencyRate
from django.core.management.base import BaseCommand
from decimal import Decimal, InvalidOperation
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from agents.models import Agent
from market.models import MarketProperty
from accounts.models import User

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


class UpdateCurrencyRatesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        fixer_url = "http://data.fixer.io/api/latest"
        access_key = "5f7f615da28e2edb57998c74ca08c4f8"
        params = {
            "access_key": access_key,
            "format": 1,
        }

        try:
            response = requests.get(fixer_url, params=params)
            data = response.json()

            if not data.get("success"):
                return Response({"error": "Failed to fetch rates from Fixer.io"}, status=400)

            base_currency = data.get("base", "EUR")
            rates = data.get("rates", {})

            for currency_code, rate in rates.items():
                try:
                    CurrencyRate.objects.update_or_create(
                        currency_code=currency_code,
                        defaults={
                            "rate": Decimal(rate),
                            "base": base_currency,
                        },
                    )
                except (InvalidOperation, TypeError):
                    print(f"Invalid rate for currency {currency_code}: {rate}")
                    continue

            return Response({"message": "Currency rates updated successfully."})

        except requests.exceptions.RequestException as e:
            return Response({"error": f"Error fetching data from Fixer.io: {str(e)}"}, status=500)
        except Exception as e:
            return Response({"error": f"Unexpected error: {str(e)}"}, status=500)


# class UpdateCurrencyRatesView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, *args, **kwargs):
#         fixer_url = "http://data.fixer.io/api/latest"
#         access_key = "5f7f615da28e2edb57998c74ca08c4f8"
#         params = {
#             "access_key": access_key,
#             "format": 1,
#         }

#         try:
#             response = requests.get(fixer_url, params=params)
#             data = response.json()

#             if not data.get("success"):
#                 return Response({"error": "Failed to fetch rates from Fixer.io"}, status=400)

#             base_currency = data["base"]
#             rates = data["rates"]

#             # Normalize rates to the base currency (e.g., USD)
#             if base_currency != "USD":
#                 usd_rate = Decimal(rates.get("USD"))
#                 if not usd_rate:
#                     return Response({"error": "USD rate not found in Fixer.io response"}, status=400)
#                 rates = {currency_code: Decimal(
#                     rate) / usd_rate for currency_code, rate in rates.items()}

#             # Update rates in the database
#             for currency_code, rate in rates.items():
#                 try:
#                     CurrencyRate.objects.update_or_create(
#                         currency_code=currency_code,
#                         defaults={"rate": rate},
#                     )
#                 except InvalidOperation:
#                     print(f"Invalid rate for currency {currency_code}: {rate}")
#                     continue

#             return Response({"message": "Currency rates updated successfully."})

#         except requests.exceptions.RequestException as e:
#             return Response({"error": f"Error fetching data from Fixer.io: {str(e)}"}, status=500)
#         except Exception as e:
#             return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=500)


class HomePageStatsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        serializer = HomePageStatsSerializer(instance={})
        return Response(serializer.data)


class CurrencyRateListView(APIView):
    def get(self, request, *args, **kwargs):
        currencies = CurrencyRate.objects.all()
        serializer = CurrencyRateSerializer(currencies, many=True)
        return Response(serializer.data)
