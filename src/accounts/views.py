from django.utils.timezone import now, timedelta
from django.utils.http import urlsafe_base64_decode
from django.shortcuts import get_object_or_404
from django.contrib.auth.tokens import default_token_generator
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_exempt
from .models import User, UserToken
import json
from django.contrib.auth import logout
from notifications.models import Device
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
import uuid


def generate_token(user):
    token = str(uuid.uuid4())
    expiration_time = now() + timedelta(hours=1)  # Token valid for 1 hour

    UserToken.objects.update_or_create(
        user=user,
        defaults={
            "token": token,
            "expires_at": expiration_time,
        }
    )
    return token


def validate_token(token):
    try:
        user_token = UserToken.objects.get(token=token)
        if user_token.is_expired():
            return JsonResponse({"error": "Token has expired"}, status=400)
        return user_token.user  # Token is valid
    except UserToken.DoesNotExist:
        return JsonResponse({"error": "Invalid token"}, status=400)


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

            # Generate token and verification link
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            expiration_time = now() + timedelta(hours=1)

            UserToken.objects.create(
                user=user, token=token, expires_at=expiration_time)

            verification_url = f"{request.scheme}://{request.get_host()}/accounts/verify-email/{uid}/{token}/"

            # Send verification email
            send_mail(
                subject="Verify Your Email Address",
                message=f"Hi {name},\n\nThank you for registering with RealVista Properties! "
                        f"Please verify your email by clicking the link below:\n\n{verification_url}\n\n"
                        f"If you did not sign up, please ignore this email.",
                from_email="RealVista Properties <noreply@realvistaproperties.com>",
                recipient_list=[email],
                fail_silently=False,
            )

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


def verify_email(request, uid, token):
    try:
        # Decode the user ID from the URL
        user_id = urlsafe_base64_decode(uid).decode()
        user = get_object_or_404(User, pk=user_id)

        # Check if the token matches and is not expired
        user_token = UserToken.objects.filter(user=user, token=token).first()
        if not user_token or user_token.is_expired():
            return JsonResponse({"error": "Invalid or expired token."}, status=400)

        # Activate the user's account
        # user.is_active = True
        user.is_email_verified = True
        user.save()

        # Optionally, delete the token after successful verification
        user_token.delete()

        return JsonResponse({"success": "Email verified successfully."}, status=200)
    except Exception as e:
        return JsonResponse({"error": "Verification failed."}, status=400)


@csrf_exempt
def resend_token(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email")

            # Check if user exists
            user = User.objects.filter(email=email).first()
            if not user:
                return JsonResponse({"error": "User with this email does not exist."}, status=400)

            # Check if the user is already verified
            if user.is_email_verified:
                return JsonResponse({"error": "This email is already verified."}, status=400)

            # Generate new token and send verification email
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            verification_url = f"{request.scheme}://{request.get_host()}/accounts/verify-email/{uid}/{token}/"

            UserToken.objects.update_or_create(
                user=user,
                defaults={"token": token},
            )

            # Send the email
            send_mail(
                subject="Resend Verification Email",
                message=f"Please verify your email using the following link: {verification_url}",
                from_email="noreply@realvistaproperties.com",
                recipient_list=[email],
            )

            return JsonResponse({"success": "A new verification token has been sent to your email."}, status=200)

        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)


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
