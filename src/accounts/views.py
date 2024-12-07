from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.timezone import now, timedelta
from django.utils.http import urlsafe_base64_decode
from django.shortcuts import get_object_or_404
from django.contrib.auth.tokens import default_token_generator
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
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
import random


def generate_verification_code():
    return str(random.randint(10000, 99999))


def generate_token(user):
    token = str(uuid.uuid4())
    expiration_time = now() + timedelta(hours=1)

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
            # token = default_token_generator.make_token(user)
            # uid = urlsafe_base64_encode(force_bytes(user.pk))
            # expiration_time = now() + timedelta(hours=1)

            token = generate_verification_code()
            expiration_time = now() + timedelta(hours=1)

            UserToken.objects.create(
                user=user, token=token, expires_at=expiration_time)

            # verification_url = f"{request.scheme}://{request.get_host()}/accounts/verify-email/{uid}/{token}/"

            # Send verification email
            send_mail(
                subject="Verify Your Email Address",
                message=f"Your verification code is: {token}\n\n"
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


@csrf_exempt
def verify_email(request, user_id):
    try:
        # Get the token (code) from the query parameters
        token = request.GET.get('code')

        if not token:
            return JsonResponse({"error": "Verification code is required."}, status=400)

        # Retrieve the user using the user_id from the URL path
        user = get_object_or_404(User, pk=user_id)

        # Check if the token exists for this user
        user_token = UserToken.objects.filter(user=user, token=token).first()

        if not user_token or user_token.is_expired():
            return JsonResponse({"error": "The code has expired."}, status=400)

        # If the token matches, verify the email and delete the token
        if user_token.token == token:
            user.is_email_verified = True
            user.save()
            user_token.delete()
            return JsonResponse({"message": "Email verified successfully."}, status=200)

        return JsonResponse({"error": "Invalid verification code."}, status=400)

    except Exception as e:
        return JsonResponse({"error": "An error occurred: " + str(e)}, status=500)


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
            # token = default_token_generator.make_token(user)
            token = generate_verification_code()
            expiration_time = now() + timedelta(hours=1)
            # uid = urlsafe_base64_encode(force_bytes(user.pk))
            # verification_url = f"{request.scheme}://{request.get_host()}/accounts/verify-email/{uid}/{token}/"

            UserToken.objects.update_or_create(
                user=user,
                defaults={"token": token, "expires_at": expiration_time},
            )

            # Send the email
            send_mail(
                subject="Resend Verification Email",
                message=f"Please verify your email using the following link: {token}",
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


def send_password_reset_email(request, email):
    try:
        # Get user by email
        user = User.objects.get(email=email)
        first_name = user.name.split()[0]

        # Generate password reset token
        token = default_token_generator.make_token(user)

        # Generate URL-safe Base64 encoding of the user's ID
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        # Construct password reset Link
        reset_url = f"https://www.realvistaproperties.com/accounts/reset/{uidb64}/{token}/"

        # Send email
        subject = "Password Reset Request"
        message = (
            f"Hi {first_name}, \n\n"
            f"We received a request to reset your password."
            f"You can reset it by clicking the link below:\n\n"
            f"{reset_url}\n\n"
            f"If you did not request this, please ignore this email.\n\n"
            f"Thank you,\n\n"
            f"Realvista Team"
        )

        send_mail(
            subject,
            message,
            "noreply@realvistaproperties.com",
            [user.email],
            fail_silently=False
        )

        return {"success": "A password reset email has been sent to your email address."}
    except User.DoesNotExist:
        return {"error": "No user is associated with this email address."}
    except Exception as e:
        return {"error": str(e)}


@csrf_exempt
def request_password_reset(request):
    if request.method == 'POST':
        try:
            # Parse JSON body
            body = json.loads(request.body)
            email = body.get('email')

            if not email:
                return JsonResponse({"error": "Email is required."}, status=400)

            # Call your email sending function
            result = send_password_reset_email(request, email)
            return JsonResponse(result)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON payload"}, status=400)
    return JsonResponse({"error": "Invalid request method"}, status=400)


@csrf_exempt
def update_password_reset(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            uidb64 = data.get('uidb64')
            token = data.get('token')
            new_password = data.get('password')

            if not uidb64 or not token or not new_password:
                return JsonResponse({'error': 'Missing required parameters.'}, status=400)

            # Decode the UID
            try:
                uid = str(urlsafe_base64_decode(uidb64).decode())
                user = User.objects.get(pk=uid)
            except (User.DoesNotExist, ValueError, TypeError):
                return JsonResponse({'error': 'Invalid UID.'}, status=400)

            # Validate the token
            if not PasswordResetTokenGenerator().check_token(user, token):
                return JsonResponse({'error': 'Invalid or expired token.'}, status=400)

            # Update the password
            user.set_password(new_password)
            user.save()

            return JsonResponse({'message': 'Password has been reset successfully.'}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON.'}, status=400)

    return JsonResponse({'error': 'Invalid request method.'}, status=400)


@csrf_exempt
def delete_account(request):
    if request.method == 'POST':
        try:
            # Parse the email from the query parameters
            email = request.GET.get('email')

            if not email:
                return JsonResponse({'error': 'Email is required in the query parameters.'}, status=400)

            # Parse JSON body to get the password
            data = json.loads(request.body)
            password = data.get("password")
            print(password)
            if not password:
                return JsonResponse({'error': 'Password is required in the request body.'}, status=400)

            try:
                # Find the user by email
                user = User.objects.get(email=email)
                first_name = user.name.split()[0]

                # Check if the password is correct
                if not user.check_password(password):
                    return JsonResponse({"error": "Incorrect password"}, status=400)

                # Delete the user account
                user.delete()

                # Send farewell email
                send_farewell_email(email, first_name)

                return JsonResponse({'success': 'Account deleted successfully, and farewell email sent.'}, status=200)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User with the provided email does not exist.'}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data.'}, status=400)

    return JsonResponse({'error': 'Invalid request method. Only POST is allowed.'}, status=405)


def send_farewell_email(email, first_name):
    """
    Sends a farewell email to the user.
    """
    subject = "We're sad to see you go"
    message = (
        f"Dear {first_name},\n\n"
        f"We regret to see you leave RealVista Properties. Your account has been successfully deleted.\n\n"
        f"If you ever decide to return, we’ll be more than happy to welcome you back.\n\n"
        f"Thank you for the time you spent with us, and we wish you all the best in your future endeavors.\n\n"
        f"Sincerely,\n"
        f"The RealVista Properties Team"
    )
    from_email = "noreply@realvistaproperties.com"

    send_mail(subject, message, from_email, [email])
