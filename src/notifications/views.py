from .serializers import LeadSerializer
from rest_framework.permissions import AllowAny
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.permissions import IsAdminUser
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from rest_framework import status
from .models import EmailNotification
from .serializers import DeviceSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q
from enterprise.models import CorporateEntity, CorporateEntityMember
from .models import Device, User
from django.shortcuts import get_object_or_404
from realvista_backend.utility import send_push_notification, send_general_notification
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Device, Lead
import json
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
def register_token(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            token = body.get('token')
            user_id = body.get('user_id')

            if not token or not user_id:
                return JsonResponse({'error': 'Token and user_id are required'}, status=400)

            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User not found'}, status=404)

            # Check if the token already exists
            existing_device = Device.objects.filter(
                Q(token=token) | Q(user=user)).first()
            if existing_device:
                if existing_device.token == token and existing_device.user == user:
                    return JsonResponse({'status': 'Token already registered for this user'}, status=200)
                else:
                    return JsonResponse({'error': 'Token is already associated with another user'}, status=409)

            # Register the token
            Device.objects.create(token=token, user=user)
            return JsonResponse({'status': 'Token registered successfully'}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'An error occurred', 'details': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_exempt
def delete_token(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        token = body.get('token')

        if token:
            try:
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
        body = json.loads(request.body)

        title = body.get('title')
        message = body.get('message')
        data = body.get('data', {})
        device_tokens = body.get('deviceTokens', [])
        group_id = body.get('groupId', '')

        if not title or not message:
            return JsonResponse({'error': 'Title and message are required'}, status=400)

        return send_push_notification(title, message, data, device_tokens, group_id)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_exempt
def send_general_notification_view(request):
    if request.method == 'POST':
        body = json.loads(request.body)

        title = body.get('title')
        message = body.get('message')
        data = body.get('data', {})

        if not title or not message:
            return JsonResponse({'error': 'Title and message are required'}, status=400)

        return send_general_notification(title, message, data)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


def get_group_members_devices(request, group_id):
    try:
        corporate_entity = get_object_or_404(
            CorporateEntity, group_id=group_id)

        group_name = corporate_entity.name

        members = CorporateEntityMember.objects.filter(
            corporate_entity=corporate_entity).select_related('user')
        users = [member.user for member in members]

        devices = Device.objects.filter(user__in=users)

        device_tokens = list(devices.values_list('token', flat=True))

        return JsonResponse({
            "status": "success",
            "group_id": group_id,
            "device_tokens": device_tokens,
            "group_name": group_name
        })

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)


def get_group_admins_devices(request, group_id):
    try:
        # Retrieve the corporate entity
        corporate_entity = get_object_or_404(
            CorporateEntity, group_id=group_id)
        group_name = corporate_entity.name

        admin_members = CorporateEntityMember.objects.filter(
            corporate_entity=corporate_entity,
            role__in=['ADMIN', 'SUPERADMIN']
        ).select_related('user')

        admin_users = [member.user for member in admin_members]

        devices = Device.objects.filter(user__in=admin_users)
        device_tokens = list(devices.values_list('token', flat=True))

        return JsonResponse({
            "status": "success",
            "group_id": group_id,
            "device_tokens": device_tokens,
            "group_name": group_name
        })

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_device(request):
    user = request.user
    device = Device.objects.filter(user=user).order_by('-created_at').first()

    if not device:
        return Response({"message": "No device found"}, status=404)

    serializer = DeviceSerializer(device)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_device(request):
    email = request.query_params.get("email")

    if not email:
        return Response({"error": "Email parameter is required"}, status=400)

    user = get_object_or_404(User, email=email)
    device = Device.objects.filter(user=user).order_by('-created_at').first()

    if not device:
        return Response({"message": "No device found for this user"}, status=404)

    serializer = DeviceSerializer(device)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def subscribe_email_notifications(request):
    if request.user.is_authenticated:
        # Authenticated user: link to user object
        notification, created = EmailNotification.objects.get_or_create(
            user=request.user
        )
    else:
        # Guest user: require an email
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required for guest users.'},
                            status=status.HTTP_400_BAD_REQUEST)

        notification, created = EmailNotification.objects.get_or_create(
            email=email
        )

    notification.receive_email_notifications = True
    notification.save()

    return Response({
        'message': 'Subscribed to email notifications.'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def unsubscribe_email_notifications(request):
    if request.user.is_authenticated:
        # Unsubscribe authenticated user
        try:
            notification = EmailNotification.objects.get(user=request.user)
            notification.delete()
            return Response({
                'message': 'Unsubscribed and data deleted for authenticated user.'
            }, status=status.HTTP_200_OK)
        except EmailNotification.DoesNotExist:
            return Response({
                'error': 'No subscription found for this user.'
            }, status=status.HTTP_404_NOT_FOUND)

    # Unsubscribe guest user via email
    email = request.data.get('email')
    if not email:
        return Response({
            'error': 'Email is required for guest unsubscription.'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        notification = EmailNotification.objects.get(email=email)
        notification.delete()
        return Response({
            'message': f'Unsubscribed and data deleted for guest: {email}.'
        }, status=status.HTTP_200_OK)
    except EmailNotification.DoesNotExist:
        return Response({
            'error': 'No subscription found for this email.'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_email_to_subscribed_users(request):
    subject = request.data.get('subject')
    message = request.data.get('message')
    from_email = "Realvista <noreply@realvistaproperties.com>"

    if not subject or not message:
        return Response({'error': 'Subject and message are required.'}, status=status.HTTP_400_BAD_REQUEST)

    subscribers = EmailNotification.objects.filter(
        receive_email_notifications=True).select_related('user')

    if not subscribers.exists():
        return Response({'message': 'No subscribers to email.'}, status=status.HTTP_204_NO_CONTENT)

    success_count = 0
    for subscriber in subscribers:
        # Determine name and email for both user types
        if subscriber.user:
            name = getattr(subscriber.user, 'name',
                           '') or subscriber.user.name or 'Dear'
            email_address = subscriber.user.email
        else:
            name = 'there'
            email_address = subscriber.email

        # Build HTML email
        html_content = render_to_string(
            'emails/notification_email.html',
            {
                'first_name': name,
                'subject': subject,
                'unsubscribe_url': f"https://realvistaproperties.com/notifications/email-notifications/unsubscribe?email={email_address}",
                'message': message
            }
        )

        # Send the email
        email = EmailMultiAlternatives(
            subject, message, from_email, [email_address])
        email.attach_alternative(html_content, "text/html")
        email.send()
        success_count += 1

    return Response({'message': f'HTML email sent to {success_count} subscribers.'}, status=status.HTTP_200_OK)


@api_view(['POST'])
def create_lead(request):
    serializer = LeadSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "Lead created successfully", "data": serializer.data},
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_all_leads(request):
    leads = Lead.objects.all().order_by('-created_at')
    serializer = LeadSerializer(leads, many=True)
    return Response(
        {"count": leads.count(), "data": serializer.data},
        status=status.HTTP_200_OK
    )


@api_view(['PUT', 'PATCH'])
def update_lead(request, pk):
    try:
        lead = Lead.objects.get(pk=pk)
    except Lead.DoesNotExist:
        return Response({"error": "Lead not found"}, status=status.HTTP_404_NOT_FOUND)

    partial = (request.method == 'PATCH')
    serializer = LeadSerializer(lead, data=request.data, partial=partial)

    if serializer.is_valid():
        serializer.save()

        return Response(
            {"message": "Lead updated successfully", "data": serializer.data},
            status=status.HTTP_200_OK
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def delete_lead(request, pk):
    try:
        lead = Lead.objects.get(pk=pk)
    except Lead.DoesNotExist:
        return Response({"error": "Lead not found"}, status=status.HTTP_404_NOT_FOUND)

    lead.delete()

    return Response({"message": "Lead deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
