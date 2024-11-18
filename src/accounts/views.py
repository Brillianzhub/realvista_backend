from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets
from django.http import JsonResponse
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from .serializers import UserSerializer
from .models import User
import json
from django.contrib.auth import logout
from notifications.models import Device


@csrf_exempt
def register_user(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            email = data.get('email')
            password = data.get('password')
            auth_provider = data.get('auth_provider', 'email')

            if not name or not email or not password:
                return JsonResponse({'error': 'All fields are required.'}, status=400)

            if User.objects.filter(email=email).exists():
                return JsonResponse({'error': 'User with this email already exists.'}, status=400)

            user = User(
                name=name,
                email=email,
                auth_provider=auth_provider
            )

            if auth_provider == 'email':
                user.password = make_password(password)

            user.save()

            return JsonResponse({
                'id': user.id,
                'name': user.name,
                'email': user.email,
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Failed to sign up: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)


@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            device_token = data.get('device_token')

            try:
                user = User.objects.get(
                    email=email, auth_provider='email')
            except User.DoesNotExist:
                return JsonResponse({'error': 'Invalid email or password'}, status=400)

            if user.check_password(password):
                if device_token:
                    device, created = Device.objects.update_or_create(
                        token=device_token,
                        defaults={'user': user}
                    )

                return JsonResponse({
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'auth_provider': user.auth_provider,
                }, status=200)
            else:
                return JsonResponse({'error': 'Invalid email or password'}, status=400)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_exempt
def google_sign_in(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            google_id = data.get('google_id')
            email = data.get('email')
            name = data.get('name')
            profile_picture = data.get('profile_picture')
            device_token = data.get('device_token')

            if not google_id or not email or not name:
                return JsonResponse({'error': 'Missing required Google user data.'}, status=400)

            # Check if user already exists
            user = User.objects.filter(email=email).first()

            if user:
                # Update existing user’s Google ID and profile picture if they exist but don't have it set
                if not user.google_id:
                    user.google_id = google_id
                if not user.profile_picture:
                    user.profile_picture = profile_picture
                user.save()

            else:
                # Create a new user
                user = User.objects.create(
                    google_id=google_id,
                    email=email,
                    name=name,
                    profile_picture=profile_picture,
                    auth_provider='google'
                )

            if device_token:
                Device.objects.update_or_create(
                    token=device_token,
                    defaults={'user': user}
                )

            return JsonResponse({
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'profile_picture': user.profile_picture
            }, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)


@csrf_exempt
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return JsonResponse({'message': 'Logged out successfully'}, status=200)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):

    user = request.user if request.user.is_authenticated else None
    if not user:
        return Response({"detail": "User not authenticated"}, status=401)

    user_data = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "auth_provider": user.auth_provider,
        "is_active": user.is_active,
        "is_staff": user.is_staff,
        "date_joined": user.date_joined,
    }
    return Response(user_data)
