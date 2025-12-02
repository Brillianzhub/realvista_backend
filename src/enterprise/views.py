from django.db.models import Sum
from .serializers import GetReleasedSlotSerializer
from .serializers import ReleasedSlotSerializer
from .models import ReleasedSlot
import json
from .models import GroupSlotAllocation
from accounts.models import User
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import GroupCoordinate
from .serializers import CoordinateListSerializer
from rest_framework import status, permissions
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from .models import CorporateEntity, CorporateEntityMember, InvitationToken
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.shortcuts import get_object_or_404
from .models import GroupProperty, GroupPropertyImage, GroupIncome, Payment, GroupSlotAllocation, GroupPropertyFile
from rest_framework.views import APIView
from .serializers import GroupIncomeSerializer, GroupExpensesSerializer
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import random
from django.core.mail import send_mail
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .serializers import CorporateEntitySerializer, GroupMemberSerializer, GroupPropertyFileSerializer, GroupPropertySerializer, GroupSlotAllocationSerializer, GroupPropertyImageUploadSerializer
import logging
from cryptography.fernet import Fernet
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
import string
import secrets
from datetime import timedelta
from django.utils import timezone


def generate_short_token(length=7):
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


encryption_key = settings.ENCRYPTION_KEY
cipher = Fernet(encryption_key)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_group(request):
    user = request.user
    data = request.data
    name = data.get('name')
    description = data.get('description', '')

    if not name:
        return Response(
            {"error": "Group name is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if CorporateEntity.objects.filter(name=name).exists():
        return Response(
            {"error": "A group with this name already exists."},
            status=status.HTTP_400_BAD_REQUEST
        )

    corporate_entity = CorporateEntity.objects.create(
        name=name,
        description=description,
        created_by=user,
    )

    CorporateEntityMember.objects.create(
        corporate_entity=corporate_entity,
        user=user,
        role="SUPERADMIN"
    )

    serializer = CorporateEntitySerializer(corporate_entity)
    return Response(
        {"message": "Group created successfully.", "group": serializer.data},
        status=status.HTTP_201_CREATED
    )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_group(request, group_id):
    try:
        user = request.user
        data = request.data
        name = data.get('name')
        description = data.get('description')

        group = CorporateEntity.objects.get(id=group_id)

        if not CorporateEntityMember.objects.filter(
            corporate_entity=group, user=user, role="SUPERADMIN"
        ).exists():
            return Response(
                {"error": "You do not have permission to update this group."},
                status=status.HTTP_403_FORBIDDEN
            )

        if name and name != group.name and CorporateEntity.objects.filter(name=name).exists():
            return Response(
                {"error": "A group with this name already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if name:
            group.name = name
        if description is not None:
            group.description = description

        group.save()

        serializer = CorporateEntitySerializer(group)
        return Response(
            {"message": "Group updated successfully.", "group": serializer.data},
            status=status.HTTP_200_OK
        )

    except CorporateEntity.DoesNotExist:
        return Response(
            {"error": "Group not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_group(request, group_id):
    try:
        user = request.user
        group = CorporateEntity.objects.get(id=group_id)

        admin_check = CorporateEntityMember.objects.filter(
            corporate_entity=group, user=user)

        if not admin_check.filter(role__iexact="SuperAdmin").exists():
            return Response(
                {"error": "You do not have permission to delete this group."},
                status=status.HTTP_403_FORBIDDEN
            )

        CorporateEntityMember.objects.filter(corporate_entity=group).delete()

        group.delete()

        return Response(
            {"message": "Group and all its members deleted successfully."},
            status=status.HTTP_200_OK
        )

    except CorporateEntity.DoesNotExist:
        return Response(
            {"error": "Group not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_group_members(request, group_id):
    try:
        group = CorporateEntity.objects.get(id=group_id)

        if not CorporateEntityMember.objects.filter(corporate_entity=group, user=request.user).exists():
            return Response(
                {"detail": "You are not a member of this group."},
                status=status.HTTP_403_FORBIDDEN
            )

        members = CorporateEntityMember.objects.filter(corporate_entity=group)

        serializer = GroupMemberSerializer(members, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except CorporateEntity.DoesNotExist:
        return Response(
            {"detail": "Group not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"detail": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def invite_member(request, pk):
    email = request.data.get("email")
    role = request.data.get("role", "MEMBER")

    try:
        validate_email(email)
        group = CorporateEntity.objects.get(id=pk)

        admin_check = CorporateEntityMember.objects.filter(
            corporate_entity=group,
            user=request.user,
            role__in=["ADMIN", "SUPERADMIN"]
        ).exists()

        if not admin_check:
            return Response(
                {"detail": "You do not have permission to invite members."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if CorporateEntityMember.objects.filter(corporate_entity=group, user__email=email).exists():
            return Response(
                {"detail": "This email is already a member of the group."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = generate_short_token()

        expires_at = timezone.now() + timedelta(hours=2)
        InvitationToken.objects.create(
            token=token,
            email=email,
            corporate_entity=group,
            role=role,
            expires_at=expires_at
        )

        email_subject = f"You've been invited to join {group.name}"
        html_content = render_to_string("emails/invite_member.html", {
            "group_name": group.name,
            "token": token
        })
        text_content = strip_tags(html_content)

        email_message = EmailMultiAlternatives(
            subject=email_subject,
            body=text_content,
            from_email="Realvista Properties <noreply@realvistaproperties.com>",
            to=[email]
        )
        email_message.attach_alternative(html_content, "text/html")
        email_message.send()

        return Response(
            {"detail": "Invitation email sent successfully."},
            status=status.HTTP_200_OK,
        )

    except ValidationError:
        return Response(
            {"detail": "Invalid email address."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except CorporateEntity.DoesNotExist:
        return Response(
            {"detail": "Group not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        logger.error(f"Error inviting member: {str(e)}")
        return Response(
            {"detail": "An unexpected error occurred."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_group(request):
    token = request.data.get("token")

    try:
        invitation = InvitationToken.objects.get(token=token)

        if invitation.is_expired():
            return Response(
                {"detail": "This token has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.user.email.lower() != invitation.email.lower():
            return Response(
                {"detail": "Invalid token or email mismatch."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        group = invitation.corporate_entity

        if CorporateEntityMember.objects.filter(corporate_entity=group, user=request.user).exists():
            return Response(
                {"detail": "You are already a member of this group."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        CorporateEntityMember.objects.create(
            corporate_entity=group,
            user=request.user,
            role=invitation.role
        )

        invitation.delete()

        return Response(
            {"detail": f"You have successfully joined the group '{group.name}'."},
            status=status.HTTP_200_OK,
        )

    except InvitationToken.DoesNotExist:
        return Response(
            {"detail": "Invalid token."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except CorporateEntity.DoesNotExist:
        return Response(
            {"detail": "Group not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return Response(
            {"detail": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class CreateGroupPropertyView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = GroupPropertySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def create_or_update_group_property(request, group_id, property_id=None):
    try:
        group = get_object_or_404(CorporateEntity, group_id=group_id)

        if not group.created_by == request.user:
            return Response(
                {"detail": "You do not have permission to manage properties for this group."},
                status=status.HTTP_403_FORBIDDEN,
            )

        data = request.data.copy()
        data['group_owner'] = group.id

        if request.method == 'POST':
            serializer = GroupPropertySerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method in ['PUT', 'PATCH']:
            if not property_id:
                return Response(
                    {"detail": "Property ID is required for updates."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            group_property = get_object_or_404(
                GroupProperty, id=property_id, group_owner=group
            )

            serializer = GroupPropertySerializer(
                group_property,
                data=data,
                partial=(request.method == 'PATCH')
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except CorporateEntity.DoesNotExist:
        return Response(
            {"detail": "Group not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    except GroupProperty.DoesNotExist:
        return Response(
            {"detail": "Property not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_group_property(request, group_id, property_id):
    try:
        try:
            property_id = int(property_id)
        except ValueError:
            return Response(
                {"detail": "Invalid property ID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        group = CorporateEntity.objects.get(group_id=group_id)
        if not group.created_by == request.user:
            return Response(
                {"detail": "You do not have permission to delete properties from this group."},
                status=status.HTTP_403_FORBIDDEN,
            )

        group_property = GroupProperty.objects.get(
            id=property_id, group_owner=group
        )

        group_property.delete()
        return Response(
            {"detail": "Property deleted successfully."},
            status=status.HTTP_200_OK,
        )

    except CorporateEntity.DoesNotExist:
        return Response(
            {"detail": "Group not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    except GroupProperty.DoesNotExist:
        return Response(
            {"detail": "Property not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_group_properties(request, group_id):
    try:
        group = CorporateEntity.objects.get(group_id=group_id)

        is_member = CorporateEntityMember.objects.filter(
            corporate_entity=group, user=request.user
        ).exists()

        if not (group.created_by == request.user or is_member):
            return Response(
                {"detail": "You do not have permission to view this group's properties."},
                status=status.HTTP_403_FORBIDDEN,
            )

        properties = GroupProperty.objects.filter(
            group_owner=group
        ).prefetch_related('incomes', 'expenses')

        serializer = GroupPropertySerializer(properties, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except CorporateEntity.DoesNotExist:
        return Response(
            {"detail": "Group not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def send_invoice_email(user_name, user_email, property, group_name, booking_reference, quantity, cost_per_slot, total_amount, currency):
    subject = "Invoice for Your Booking"
    message = render_to_string("emails/invoice.html", {
        "user_name": user_name,
        "property": property,
        "group_name": group_name,
        "booking_reference": booking_reference,
        "quantity": quantity,
        "cost_per_slot": cost_per_slot,
        "total_amount": total_amount,
        "currency": currency
    })
    email = EmailMessage(
        subject,
        message,
        "Realvista <noreply@realvistaproperties.com>",
        [user_email],
    )
    email.content_subtype = "html"
    email.send()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def book_slot(request, property_id):
    try:
        property = GroupProperty.objects.get(id=property_id)
        slot_price = property.slot_price
        slots_to_book = request.data.get('slots_owned')
        booking_reference = request.data.get('booking_reference')
        user_name = request.data.get('user_name')
        booking_reference = request.data.get('booking_reference')

        if not slots_to_book or not isinstance(slots_to_book, int):
            return Response(
                {"error": "Invalid or missing 'slots_owned' value."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        available_slots = property.available_slots()

        if available_slots is None:
            return Response(
                {"error": "Group property does not have available slots information."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if slots_to_book > available_slots:
            return Response({"error": "Not enough available slots"}, status=status.HTTP_400_BAD_REQUEST)

        booking = GroupSlotAllocation.objects.create(
            property=property,
            user=request.user,
            slots_owned=slots_to_book,
            booking_reference=booking_reference,
            total_cost=slots_to_book * slot_price
        )

        send_invoice_email(
            user_name=user_name,
            user_email=request.user.email,
            property=property.title,
            group_name=property.group_owner,
            booking_reference=booking_reference,
            quantity=slots_to_book,
            cost_per_slot=slot_price,
            total_amount=slots_to_book * slot_price,
            currency=property.currency
        )

        return Response(GroupSlotAllocationSerializer(booking).data, status=status.HTTP_201_CREATED)

    except GroupProperty.DoesNotExist:
        return Response({"error": "Group property not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_all_bookings(request, property_id):
    try:
        if not request.user:
            return Response(
                {"detail": "You do not have permission to access this resource."},
                status=status.HTTP_403_FORBIDDEN,
            )

        bookings = GroupSlotAllocation.objects.select_related(
            'user', 'property').filter(property_id=property_id)

        if not bookings.exists():
            return Response(
                {"detail": "No bookings found for this property."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = GroupSlotAllocationSerializer(bookings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def confirm_payment(request, booking_id):
    try:
        booking = GroupSlotAllocation.objects.get(id=booking_id)

        if not request.user:
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN,
            )

        booking.status = "booked"
        booking.save()

        return Response(
            {"detail": "Payment confirmed successfully.", "status": booking.status},
            status=status.HTTP_200_OK,
        )
    except GroupSlotAllocation.DoesNotExist:
        return Response(
            {"detail": "Booking not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def make_payment(request, booking_id):
    try:
        booking = GroupSlotAllocation.objects.get(
            id=booking_id, user=request.user)

        payment_status = random.choice(['successful', 'failed'])

        payment = Payment.objects.create(
            booking=booking,
            user=request.user,
            amount_paid=booking.total_cost,
            payment_status=payment_status,
            transaction_id=str(random.randint(100000, 999999))
        )

        if payment_status == 'successful':
            booking.status = 'booked'
            booking.save()

        return Response({"payment_status": payment_status, "transaction_id": payment.transaction_id}, status=status.HTTP_200_OK)

    except GroupSlotAllocation.DoesNotExist:
        return Response({"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_property_income(request):
    try:
        data = request.data
        property_id = data.get('property_id')

        if not property_id:
            return Response(
                {"detail": "Property ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            group_property = GroupProperty.objects.get(id=property_id)
        except GroupProperty.DoesNotExist:
            return Response(
                {"detail": "The specified property does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = GroupIncomeSerializer(data=data)
        if serializer.is_valid():
            serializer.save(property=group_property)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_property_expense(request):
    try:
        data = request.data
        property_id = data.get('property_id')

        if not property_id:
            return Response(
                {"detail": "Property ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            group_property = GroupProperty.objects.get(id=property_id)
        except GroupProperty.DoesNotExist:
            return Response(
                {"detail": "The specified property does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = GroupExpensesSerializer(data=data)
        if serializer.is_valid():
            serializer.save(property=group_property)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class GroupPropertyImageUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        property_id = request.data.get('property')
        if not property_id:
            return Response({'error': 'Property ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            property_instance = GroupProperty.objects.get(id=property_id)
        except GroupProperty.DoesNotExist:
            return Response({'error': 'Invalid property ID'}, status=status.HTTP_404_NOT_FOUND)

        if 'image' not in request.FILES:
            return Response({'error': 'No image files provided'}, status=status.HTTP_400_BAD_REQUEST)

        images = request.FILES.getlist('image')

        saved_images = []
        for image in images:
            property_image = GroupPropertyImage(
                property=property_instance, image=image)
            property_image.save()
            saved_images.append(
                GroupPropertyImageUploadSerializer(property_image).data)

        return Response(
            {'status': 'Images uploaded successfully', 'data': saved_images},
            status=status.HTTP_201_CREATED
        )


class MakeAdminView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, group_id):
        user = request.user
        member_id = request.data.get("member_id")

        if not member_id:
            return Response({"detail": "Member ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        member = get_object_or_404(CorporateEntityMember, id=member_id)

        try:
            superadmin = CorporateEntityMember.objects.get(
                user=user, corporate_entity=member.corporate_entity
            )
            if superadmin.role != "SUPERADMIN":
                return Response({"detail": "Only SuperAdmins can promote users to Admin."}, status=status.HTTP_403_FORBIDDEN)
        except CorporateEntityMember.DoesNotExist:
            return Response({"detail": "You are not a member of this entity."}, status=status.HTTP_403_FORBIDDEN)

        if member.role == "ADMIN":
            return Response({"detail": "User is already an admin."}, status=status.HTTP_400_BAD_REQUEST)

        member.role = "ADMIN"
        member.save()
        return Response({"detail": f"{member.user.email} is now an admin."}, status=status.HTTP_200_OK)


class RemoveAdminView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, group_id):
        user = request.user
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"detail": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        member = get_object_or_404(CorporateEntityMember, id=user_id)

        try:
            superadmin = CorporateEntityMember.objects.get(
                user=user, corporate_entity=member.corporate_entity
            )
            if superadmin.role != 'SUPERADMIN':
                return Response({"detail": "Only SuperAdmins can demote Admins."}, status=status.HTTP_403_FORBIDDEN)
        except CorporateEntityMember.DoesNotExist:
            return Response({"detail": "You are not a member of this entity."}, status=status.HTTP_403_FORBIDDEN)

        if member.role != 'ADMIN':
            return Response({"detail": "User is not an admin."}, status=status.HTTP_400_BAD_REQUEST)

        member.role = 'MEMBER'
        member.save()

        return Response({"detail": f"{member.user.email} is no longer an admin."}, status=status.HTTP_200_OK)


class RemoveUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, group_id):
        user = request.user
        member_id = request.data.get('member_id')
        if not member_id:
            return Response({"detail": "Member ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        member = get_object_or_404(CorporateEntityMember, id=member_id)

        try:
            superadmin = CorporateEntityMember.objects.get(
                user=user, corporate_entity=member.corporate_entity
            )
            if superadmin.role != 'SUPERADMIN':
                return Response({"detail": "Only SuperAdmins can remove users."}, status=status.HTTP_403_FORBIDDEN)
        except CorporateEntityMember.DoesNotExist:
            return Response({"detail": "You are not a member of this entity."}, status=status.HTTP_403_FORBIDDEN)

        member.delete()

        return Response({"detail": f"{member.user.email} has been removed from the corporate entity."}, status=status.HTTP_200_OK)


class GroupPropertyFileUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        property_id = request.data.get('property')
        if not property_id:
            return Response({'error': 'Property ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            property_instance = GroupProperty.objects.get(id=property_id)
        except GroupProperty.DoesNotExist:
            return Response({'error': 'Invalid property ID'}, status=status.HTTP_404_NOT_FOUND)

        if 'file' not in request.FILES:
            return Response({'error': 'No files provided'}, status=status.HTTP_400_BAD_REQUEST)

        files = request.FILES.getlist('file')
        saved_files = []

        for file in files:
            file_name = file.name

            property_file = GroupPropertyFile(
                property=property_instance,
                file=file,
                name=file_name
            )
            property_file.save()

            saved_files.append(
                GroupPropertyFileSerializer(property_file).data)

        return Response(
            {'status': 'Files uploaded successfully', 'data': saved_files},
            status=status.HTTP_201_CREATED
        )


class GroupPropertyFileDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, file_id, *args, **kwargs):
        try:
            file_instance = GroupPropertyFile.objects.get(id=file_id)
        except GroupPropertyFile.DoesNotExist:
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

        file_instance.delete()
        return Response({'status': 'File deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


class CoordinateBulkCreateAPIView(APIView):
    def post(self, request, *args, **kwargs):

        serializer = CoordinateListSerializer(data=request.data)
        if serializer.is_valid():
            created_coordinates = serializer.save()
            return Response(
                {
                    "message": f"{len(created_coordinates)} coordinates saved successfully!",
                    "data": [
                        {
                            "id": coord.id,
                            "property": coord.property.id,
                            "latitude": coord.latitude,
                            "longitude": coord.longitude
                        }
                        for coord in created_coordinates
                    ]
                },
                status=status.HTTP_201_CREATED
            )

        print("Validation errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
def delete_coordinate(request, coordinate_id):
    if request.method == "DELETE":
        coordinate = get_object_or_404(GroupCoordinate, id=coordinate_id)
        coordinate.delete()
        return JsonResponse({"message": "Coordinate deleted successfully"}, status=200)
    return JsonResponse({"error": "Invalid request method"}, status=400)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_slot_booking(request, booking_id):

    try:
        booking = GroupSlotAllocation.objects.get(
            id=booking_id, user=request.user)
    except GroupSlotAllocation.DoesNotExist:
        return Response({"detail": "Booking not found or does not belong to you."}, status=status.HTTP_404_NOT_FOUND)

    if booking.status != 'pending':
        return Response({"detail": "Only pending slots can be cancelled."}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        booking.status = 'cancelled'
        booking.save()

    return Response({"detail": "Pending slot booking cancelled successfully."}, status=status.HTTP_200_OK)


@csrf_exempt
@require_http_methods(["POST"])
def transfer_slots_view(request):
    try:
        data = json.loads(request.body)
        allocation_ids = data.get("allocation_id")
        target_user_email = data.get("target_user_email")
        slots_to_transfer = int(data.get("slots_to_transfer", 0))

        if not allocation_ids or not target_user_email or not slots_to_transfer:
            return JsonResponse({"status": "error", "message": "Missing required fields."}, status=400)

        allocation_ids = [int(aid) for aid in allocation_ids.split(",")]

        allocations = GroupSlotAllocation.objects.filter(
            id__in=allocation_ids).order_by("id")

        if not allocations.exists():
            return JsonResponse({"status": "error", "message": "Allocations not found."}, status=404)

        try:
            target_user = User.objects.get(email=target_user_email)
        except User.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Target user not found."}, status=404)

        slots_remaining = slots_to_transfer

        with transaction.atomic():
            for allocation in allocations:
                if slots_remaining <= 0:
                    break  # Stop once enough slots are transferred

                # ✅ Use the correct field: `slots_owned`
                available_slots = allocation.slots_owned
                if available_slots <= 0:
                    continue  # Skip allocations with zero slots

                # Transfer only the needed number of slots
                slots_to_move = min(slots_remaining, available_slots)
                target_allocation = allocation.transfer_slots(
                    target_user, slots_to_move)

                # Set custom attributes for the signal
                target_allocation._is_transfer = True
                target_allocation._target_user = target_user
                target_allocation.save()

                slots_remaining -= slots_to_move  # Reduce the remaining slots to transfer

            if slots_remaining > 0:
                return JsonResponse(
                    {"status": "error", "message": "Not enough slots available for transfer."}, status=400
                )

        return JsonResponse({
            "status": "success",
            "message": f"Successfully transferred {slots_to_transfer} slots to {target_user.email}."
        })

    except ObjectDoesNotExist:
        return JsonResponse({"status": "error", "message": "Allocation not found."}, status=404)
    except ValidationError as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": f"An unexpected error occurred: {str(e)}"}, status=500)



@api_view(['GET'])
@permission_classes([IsAuthenticated])  
def get_released_slots(request):
    property_id = request.query_params.get('property_id')  

    if not property_id:
        return Response(
            {'error': 'Property ID is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    slots = ReleasedSlot.objects.filter(
        property_id=property_id,
        is_available=True
    ).order_by('-released_at')

    serializer = GetReleasedSlotSerializer(slots, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def release_slots(request):

    data = request.data.copy()
    data['user'] = request.user.id

    serializer = ReleasedSlotSerializer(data=data)

    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_total_released_slots_for_authenticated_user(request):
    user = request.user
    property_id = request.query_params.get(
        'property') 

    if not property_id:
        return Response({
            'error': 'Property ID is required.'
        }, status=status.HTTP_400_BAD_REQUEST)

    total_slots = ReleasedSlot.objects.filter(
        user=user,
        property_id=property_id,
        is_available=True
    ).aggregate(total_released=Sum('number_of_slots'))

    total_released = total_slots['total_released'] or 0

    return Response({
        'user': user.email,
        'property': property_id,
        'total_released_slots': total_released
    }, status=status.HTTP_200_OK)
