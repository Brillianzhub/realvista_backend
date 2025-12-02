import requests
from .serializers import AdminReferralPayoutSerializer
from rest_framework.permissions import IsAdminUser
from .serializers import ReferralPayoutRequestSerializer, ReferralPayoutSerializer
from .models import ReferralPayout
from decimal import Decimal
from django.db import transaction
from django.core.exceptions import PermissionDenied
from .serializers import AdminProfileSerializer
from rest_framework import generics, permissions
from firebase_admin import credentials
from django.conf import settings
import firebase_admin
from firebase_admin import auth as firebase_auth
from agents.serializers import AgentSerializer, AgentStatSerializer
from subscriptions.serializers import UserSubscriptionSerializer
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from django.contrib.auth.decorators import login_required
from subscriptions.models import UserSubscription
from accounts.models import PasswordResetOTP, User
from datetime import datetime
from django.utils import timezone
from .models import PasswordResetOTP
from django.utils.html import strip_tags
from .utils import send_password_change_email
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.utils.timezone import now, timedelta, make_aware
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_exempt
from .models import User, UserToken, Profile, UserPreference, Referral
from agents.models import Agent
import json
from django.contrib.auth import logout
from notifications.models import Device
from django.core.mail import send_mail
import uuid
import random
from .serializers import ProfileSerializer, UserPreferenceSerializer

from enterprise.serializers import MembershipSerializer
from enterprise.models import CorporateEntityMember

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string



def generate_verification_code():
    return str(random.randint(10000, 99999))


def generate_otp():
    return random.randint(10000, 99999)


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
        return user_token.user
    except UserToken.DoesNotExist:
        return JsonResponse({"error": "Invalid token"}, status=400)


def send_password_reset_email(request, email):
    try:
        user = User.objects.get(email=email)
        first_name = user.name.split()[0]

        otp = generate_otp()
        expires_at = timezone.now() + timedelta(minutes=10)

        PasswordResetOTP.objects.filter(user=user).delete()

        PasswordResetOTP.objects.create(
            user=user, otp=otp, expires_at=expires_at)

        subject = "Password Reset OTP"

        html_message = render_to_string("emails/password_reset_email.html", {
            "first_name": first_name,
            "otp": otp
        })
        plain_message = strip_tags(html_message)

        email = EmailMultiAlternatives(
            subject,
            plain_message,
            "Realvista <noreply@realvistaproperties.com>",
            [user.email]
        )
        email.attach_alternative(html_message, "text/html")
        email.send()

        return {"success": "A password reset OTP has been sent to your email address."}
    except User.DoesNotExist:
        return {"error": "No user is associated with this email address."}
    except Exception as e:
        return {"error": str(e)}


def process_referral(user, referrer_code):

    if not referrer_code:
        return None

    try:
        referrer = User.objects.get(referral_code=referrer_code)

        # Prevent self-referral
        if referrer == user:
            return JsonResponse(
                {'error': 'You cannot refer yourself.'},
                status=400
            )

        # Create the referral with transaction safety
        with transaction.atomic():
            Referral.objects.create(referrer=referrer, referred_user=user)
            user.referrer = referrer
            user.save()

        print(f"Referral created: {referrer.referral_code} → {user.email}")
        return None

    except User.DoesNotExist:
        return JsonResponse(
            {'error': 'Invalid referral code.'},
            status=400
        )


@csrf_exempt
def register_user(request):
    if request.method == 'POST':
        try:
            if request.content_type.startswith('multipart/form-data'):
                data = request.POST
                files = request.FILES
            else:
                data = json.loads(request.body)
                files = None

            referrer_code = request.GET.get('ref') or data.get('referrer_code')

            user_data = {
                'name': data.get('name'),
                'first_name': data.get('first_name'),
                'email': data.get('email'),
                'password': data.get('password'),
                'auth_provider': data.get('auth_provider', 'email')
            }

            if not all([user_data['name'], user_data['email'], user_data['password']]):
                return JsonResponse({'error': 'Name, email and password are required.'}, status=400)

            if User.objects.filter(email=user_data['email']).exists():
                return JsonResponse({'error': 'Email already exists.'}, status=400)

            user = User(**user_data)
            if user_data['auth_provider'] == 'email':
                user.password = make_password(user_data['password'])
            user.save()

            profile_data = {
                'phone_number': data.get('phone_number'),
                'whatsapp_number': data.get('whatsapp_number'),
            }

            if files and 'avatar' in files:
                profile_data['avatar'] = files['avatar']

            Profile.objects.create(user=user, **profile_data)

            if data.get('is_agent', False):
                Agent.objects.create(
                    user=user,
                    agency_name=data.get('agency_name'),
                    agency_address=data.get('agency_address'),
                    phone_number=data.get('phone_number'),
                    whatsapp_number=data.get('whatsapp_number'),
                    experience_years=data.get('experience_years', 0),
                    bio=data.get('bio', ''),
                    preferred_contact_mode=data.get(
                        'preferred_contact_mode', 'phone'),
                    avatar=profile_data.get('avatar')
                )

            referral_response = process_referral(user, referrer_code)

            if referral_response:
                return referral_response

            token = generate_otp()
            expiration_time = now() + timedelta(minutes=10)

            UserToken.objects.create(
                user=user, token=token, expires_at=expiration_time)

            context = {
                'first_name': user_data['first_name'], 'token': token}
            html_message = render_to_string(
                'emails/verify_email.html', context)
            plain_message = strip_tags(html_message)

            send_mail(
                subject="Verify Your Email Address",
                message=plain_message,
                from_email="Realvista <noreply@realvistaproperties.com>",
                recipient_list=[user_data['email']],
                fail_silently=False,
                html_message=html_message,
            )

            return JsonResponse({
                'id': user.id,
                'name': user.name,
                'first_name': user.first_name,
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
        token = request.GET.get('code')

        if not token:
            return JsonResponse({"error": "Verification code is required."}, status=400)

        user = get_object_or_404(User, pk=user_id)

        user_token = UserToken.objects.filter(user=user, token=token).first()

        if not user_token or user_token.is_expired():
            return JsonResponse({"error": "The code has expired."}, status=400)

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

            user = User.objects.filter(email=email).first()
            if not user:
                return JsonResponse({"error": "User with this email does not exist."}, status=400)

            if user.is_email_verified:
                return JsonResponse({"error": "This email is already verified."}, status=400)

            token = generate_verification_code()
            expiration_time = now() + timedelta(hours=1)

            UserToken.objects.update_or_create(
                user=user,
                defaults={"token": token, "expires_at": expiration_time},
            )

            # Send the email
            send_mail(
                subject="Resend Verification Email",
                message=f"Please verify your email using the following link: {token}",
                from_email="Realvista <noreply@realvistaproperties.com>",
                recipient_list=[email],
            )

            return JsonResponse({"success": "A new verification token has been sent to your email."}, status=200)

        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)


@csrf_exempt
def login_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)

    email = data.get('email')
    password = data.get('password')
    device_token = data.get('device_token')

    if not email or not password:
        return JsonResponse({'error': 'Email and password are required'}, status=400)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Invalid email or password'}, status=400)

    if not user.check_password(password):
        return JsonResponse({'error': 'Invalid email or password'}, status=400)

    # Register device token if available and valid
    if device_token:
        try:
            Device.objects.update_or_create(
                token=device_token,
                defaults={'user': user}
            )
        except Exception as e:
            print("Device registration failed:", str(e))

    # Get or create authentication token
    token, created = Token.objects.get_or_create(user=user)

    # Get optional related data
    profile = Profile.objects.filter(user=user).first()
    preference = UserPreference.objects.filter(user=user).first()

    serialized_profile = ProfileSerializer(profile).data if profile else None
    serialized_preference = UserPreferenceSerializer(
        preference).data if preference else None

    return JsonResponse({
        'id': user.id,
        'name': user.name,
        'first_name': user.first_name,
        'email': user.email,
        'auth_provider': user.auth_provider,
        'is_active': user.is_active,
        'is_staff': user.is_staff,
        "is_phone_verified": user.is_phone_verified,
        "is_identity_verified": user.is_identity_verified,
        "is_email_verified": user.is_email_verified,
        'date_joined': user.date_joined,
        'profile': serialized_profile,
        'preference': serialized_preference,
        'token': token.key
    }, status=200)


@csrf_exempt
def google_sign_in(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            google_id = data.get('google_id')
            email = data.get('email')
            name = data.get('name')
            first_name = data.get('first_name')

            if not google_id or not email or not name:
                return JsonResponse({'error': 'Missing required Google user data.'}, status=400)

            user, created = User.objects.get_or_create(email=email, defaults={
                'google_id': google_id,
                'name': name,
                'first_name': first_name,
                'auth_provider': 'google',
                'is_email_verified': True
            })

            if not created and not user.google_id:
                user.google_id = google_id
                user.save()

            token, _ = Token.objects.get_or_create(user=user)

            return JsonResponse({
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'token': token.key
            }, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)



@csrf_exempt
def apple_sign_in(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            apple_user = data.get('apple_user')
            email = data.get('email')
            first_name = data.get('first_name', '')
            last_name = data.get('last_name', '')
            identity_token = data.get('identity_token')

            if not apple_user or not identity_token:
                return JsonResponse({'error': 'Missing required Apple user data.'}, status=400)

            # Decode and verify Apple identity token (optional but recommended)
            # decoded_token = jwt.decode(identity_token, options={"verify_signature": False})
            # You can add signature verification later if you want strict validation

            # Try to find existing user by Apple ID or email
            user = None
            if email:
                user = User.objects.filter(email=email).first()
            if not user:
                user = User.objects.filter(apple_id=apple_user).first()

            # Create user if not exists
            if not user:
                user = User.objects.create(
                    apple_id=apple_user,
                    email=email or f"{apple_user}@appleuser.com",
                    first_name=first_name,
                    name=f"{first_name} {last_name}".strip() or "Apple User",
                    auth_provider='apple',
                    is_email_verified=True
                )

            # Update apple_id if missing
            if not user.apple_id:
                user.apple_id = apple_user
                user.save()

            # Get or create auth token
            token, _ = Token.objects.get_or_create(user=user)

            return JsonResponse({
                'token': token.key,
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                }
            }, status=200)

        except Exception as e:
            # print("APPLE SIGN-IN ERROR:", e)
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

    referred_users_count = Referral.objects.filter(referrer=user).count()

    memberships = CorporateEntityMember.objects.filter(user=user)
    serialized_memberships = MembershipSerializer(memberships, many=True).data

    profile = Profile.objects.filter(user=user).first()
    preference = UserPreference.objects.filter(user=user).first()

    subscription = UserSubscription.objects.filter(user=user).first()

    # 👈 Check if user is an agent
    agent = Agent.objects.filter(user=user).first()
    serialized_agent = AgentStatSerializer(
        agent).data if agent else None

    user_data = {
        "id": user.id,
        "name": user.name,
        "first_name": user.first_name,
        "email": user.email,
        "auth_provider": user.auth_provider,
        "total_referral_earnings": user.total_referral_earnings,
        "referral_code": user.referral_code,
        "referrer": user.referrer.email if user.referrer else None,
        "referred_users_count": referred_users_count,
        "is_active": user.is_active,
        "is_phone_verified": user.is_phone_verified,
        "is_identity_verified": user.is_identity_verified,
        "is_email_verified": user.is_email_verified,
        "is_staff": user.is_staff,
        "date_joined": user.date_joined,
        "groups": serialized_memberships,
        "profile": ProfileSerializer(profile).data if profile else None,
        "preference": UserPreferenceSerializer(preference).data if preference else None,
        "subscription": UserSubscriptionSerializer(subscription).data if subscription else None,
        "agent": serialized_agent
    }

    return Response(user_data)


@csrf_exempt
def request_password_reset(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            email = body.get('email')

            if not email:
                return JsonResponse({"error": "Email is required."}, status=400)

            result = send_password_reset_email(request, email)
            return JsonResponse(result)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON payload"}, status=400)
    return JsonResponse({"error": "Invalid request method"}, status=400)


@csrf_exempt
def verify_otp(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email")
            otp = data.get("otp")

            if not email or not otp:
                return JsonResponse({"error": "Email and OTP are required."}, status=400)

            try:
                otp_record = PasswordResetOTP.objects.get(
                    user__email=email, otp=otp)

                if otp_record.expires_at < make_aware(datetime.now()):
                    return JsonResponse({"error": "OTP has expired."}, status=400)

                otp_record.delete()

                return JsonResponse({"message": "OTP verified successfully. You can now reset your password."}, status=200)

            except PasswordResetOTP.DoesNotExist:
                return JsonResponse({"error": "Invalid OTP."}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format."}, status=400)

    return JsonResponse({"error": "Invalid request method."}, status=400)


@csrf_exempt
def update_password_reset(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            new_password = data.get('password')

            if not email or not new_password:
                return JsonResponse({'error': 'Missing required parameters.'}, status=400)

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return JsonResponse({'error': 'No account found with this email.'}, status=400)

            if len(new_password) < 8:
                return JsonResponse({'error': 'Password must be at least 6 characters long.'}, status=400)

            user.set_password(new_password)
            user.save()

            return JsonResponse({'message': 'Password has been reset successfully.'}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format.'}, status=400)

    return JsonResponse({'error': 'Invalid request method.'}, status=400)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if not user.check_password(old_password):
            return Response({"error": "Old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response({"error": "New passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 6:
            return Response({"error": "New password must be at least 6 characters long"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        send_password_change_email(user)

        return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)

    if request.method == 'GET':
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

    if request.method == 'PUT':
        data = request.data.copy()

        # Update profile avatar if provided
        if 'avatar' in request.FILES:
            avatar = request.FILES['avatar']
            profile.avatar = avatar

        serializer = ProfileSerializer(profile, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()

            try:
                agent = user.agent_profile

                # Update overlapping fields
                if profile.avatar:
                    agent.avatar = profile.avatar
                if profile.phone_number:
                    agent.phone_number = str(profile.phone_number)
                if profile.whatsapp_number:
                    agent.whatsapp_number = profile.whatsapp_number

                # Update bio if provided in request
                bio = data.get('bio')
                if bio is not None:
                    agent.bio = bio

                agent.save()
            except Agent.DoesNotExist:
                pass

            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
def delete_account(request):
    if request.method == 'POST':
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Token '):
            return JsonResponse({'error': 'Authorization token is missing or invalid.'}, status=401)

        token_key = auth_header.split(' ')[1]
        try:
            token = Token.objects.get(key=token_key)
            user = token.user
            email = user.email
            first_name = user.name.split()[0]

        except Token.DoesNotExist:
            return JsonResponse({'error': 'Invalid token.'}, status=401)

        send_acknowledgment_email(email, first_name)

        forward_deletion_request(email, first_name)

        return JsonResponse({
            'success': (
                'Your account deletion request has been received. '
                'It will be processed within 14 days. You will still have access to your account during this period. '
                'We recommend deleting any saved documents, as they will no longer be available once your account is permanently removed.'
            )
        }, status=200)


    return JsonResponse({'error': 'Invalid request method. Only POST is allowed.'}, status=405)


def send_acknowledgment_email(email, first_name):
    subject = "Account Deletion Request Received"
    html_message = render_to_string(
        "emails/account_deletion.html", {"first_name": first_name})
    plain_message = strip_tags(html_message)
    from_email = "Realvista <noreply@realvistaproperties.com>"

    send_mail(subject, plain_message, from_email,
              [email], html_message=html_message)


def forward_deletion_request(email, first_name):
    subject = "User Account Deletion Request"
    message = (
        f"User {first_name} ({email}) has requested to delete their account.\n\n"
        f"The deletion process should be completed within 3 months. Please ensure the necessary actions are taken.\n\n"
        f"Sincerely,\n"
        f"Automated System - Realvista Properties"
    )
    from_email = "Realvista <noreply@realvistaproperties.com>"
    admin_email = "contact@realvistaproperties.com"

    send_mail(subject, message, from_email, [admin_email])


class UserPreferenceUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, user):
        return UserPreference.objects.get(user=user)

    def put(self, request, *args, **kwargs):
        user = request.user
        preference = self.get_object(user)

        serializer = UserPreferenceSerializer(
            preference, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def submit_referrer_code(request):
    try:
        data = json.loads(request.body)
        referrer_code = data.get('referrer_code')

        user = request.user

        if not referrer_code:
            return JsonResponse({'error': 'Referral code is required.'}, status=400)

        if user.referrer is not None:
            return JsonResponse({'error': 'Referral code has already been submitted.'}, status=400)

        try:
            referrer = User.objects.get(referral_code=referrer_code)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Invalid referral code.'}, status=400)

        if user == referrer:
            return JsonResponse({'error': 'You cannot refer yourself.'}, status=400)

        if Referral._is_referral_cycle(referrer, user):
            return JsonResponse({'error': 'A referral cycle is not allowed.'}, status=400)

        user.referrer = referrer
        user.save()

        Referral.objects.create(referrer=referrer, referred_user=user)

        return JsonResponse({'message': 'Referral code successfully submitted.'}, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Failed to submit referral code: {str(e)}'}, status=500)


if not firebase_admin._apps:
    cred = credentials.Certificate(settings.FIREBASE_ADMIN_CREDENTIAL)
    firebase_admin.initialize_app(cred)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def verify_phone(request):
    user = request.user
    phone = request.data.get("phone")
    id_token = request.data.get("firebase_id_token")

    if not phone or not id_token:
        return Response({"detail": "Phone and Firebase ID token required."}, status=400)

    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        firebase_phone = decoded_token.get("phone_number")

        if not firebase_phone or firebase_phone != phone:
            return Response({"detail": "Phone number mismatch."}, status=400)

        # Optional: ensure it matches the user profile number
        if str(user.profile.phone_number) != phone:
            return Response({"detail": "Provided phone doesn't match user profile."}, status=400)

        user.is_phone_verified = True
        user.save()
        return Response({"detail": "Phone verified successfully."})
    except Exception as e:
        return Response({"detail": str(e)}, status=400)


class AdminProfileDetailView(generics.RetrieveAPIView):
    serializer_class = AdminProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        user = self.request.user
        if hasattr(user, 'admin_profile'):
            return user.admin_profile
        raise PermissionDenied("You do not have an admin profile.")


class ReferralPayoutView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payouts = ReferralPayout.objects.filter(
            user=request.user).order_by('-created_at')
        serializer = ReferralPayoutSerializer(payouts, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ReferralPayoutRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        amount = serializer.validated_data['amount']

        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=request.user.pk)

            if amount > user.total_referral_earnings:
                return Response(
                    {"error": "Requested amount exceeds available referral earnings"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if amount < Decimal('5000.00'):
                return Response(
                    {"error": "Minimum payout amount is NGN5000.00"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            payout = ReferralPayout.objects.create(
                user=user,
                amount=amount,
                payment_method=serializer.validated_data['payment_method'],
                account_details=serializer.validated_data['account_details'],
            )

            user.total_referral_earnings -= amount
            user.save()

        return Response(
            ReferralPayoutSerializer(payout).data,
            status=status.HTTP_201_CREATED
        )


class AdminPayoutManagementView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        # Get query parameters for filtering
        status_filter = request.query_params.get('status', None)
        user_email = request.query_params.get('user_email', None)
        min_amount = request.query_params.get('min_amount', None)
        max_amount = request.query_params.get('max_amount', None)

        queryset = ReferralPayout.objects.all().order_by('-created_at')

        # Apply filters
        if status_filter:
            queryset = queryset.filter(status=status_filter.lower())
        if user_email:
            queryset = queryset.filter(user__email__icontains=user_email)
        if min_amount:
            queryset = queryset.filter(amount__gte=min_amount)
        if max_amount:
            queryset = queryset.filter(amount__lte=max_amount)

        serializer = AdminReferralPayoutSerializer(queryset, many=True)
        return Response(serializer.data)

    def patch(self, request, payout_id):
        try:
            payout = ReferralPayout.objects.get(id=payout_id)
        except ReferralPayout.DoesNotExist:
            return Response(
                {"error": "Payout request not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AdminReferralPayoutSerializer(
            payout,
            data=request.data,
            partial=True
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        new_status = request.data.get('status')
        if new_status:
            if new_status == 'processed' and payout.status != 'approved':
                return Response(
                    {"error": "Only approved payouts can be marked as processed"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if new_status == 'approved' and payout.status not in ['pending', 'rejected']:
                return Response(
                    {"error": "Only pending or rejected payouts can be approved"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer.save()

        # Update processed_at if status changed to processed
        if new_status == 'processed':
            payout.processed_at = timezone.now()
            payout.save()

        return Response(serializer.data)
