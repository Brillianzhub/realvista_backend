from django.conf import settings
from firebase_admin import credentials
import firebase_admin
from course.models import UserProgress
from django.utils import timezone
from firebase_admin import messaging
from notifications.models import Device
from django.http import JsonResponse
import requests
import json
from django.db import transaction
from projects.models import Project
from order.models import Order
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from io import BytesIO
from reportlab.pdfgen import canvas
from datetime import datetime


def send_invoice_email(user_name, user_email, project_name, quantity, cost_per_slot, total_amount):
    try:
        # Generate PDF invoice
        buffer = BytesIO()
        pdf_canvas = canvas.Canvas(buffer)

        x = 100
        y = 750
        line_spacing = 20

        pdf_canvas.setFont("Helvetica-Bold", 14)
        pdf_canvas.drawString(x, y, f"INVOICE")
        y -= line_spacing

        # Invoice details
        pdf_canvas.setFont("Helvetica", 12)
        pdf_canvas.drawString(x, y, f"Invoice No: 001234")
        y -= line_spacing
        pdf_canvas.drawString(
            x, y, f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        y -= line_spacing * 2

        # Bill To
        pdf_canvas.setFont("Helvetica-Bold", 12)
        pdf_canvas.drawString(x, y, "BILL TO:")
        y -= line_spacing
        pdf_canvas.setFont("Helvetica", 12)
        pdf_canvas.drawString(x, y, user_name)
        y -= line_spacing
        pdf_canvas.drawString(x, y, user_email)
        y -= line_spacing * 2

        # From
        pdf_canvas.setFont("Helvetica-Bold", 12)
        pdf_canvas.drawString(x, y, "FROM:")
        y -= line_spacing
        pdf_canvas.setFont("Helvetica", 12)
        pdf_canvas.drawString(x, y, "Realvista GmbH")
        y -= line_spacing * 2

        # Project Details
        pdf_canvas.setFont("Helvetica-Bold", 12)
        pdf_canvas.drawString(x, y, "PROJECT DETAILS:")
        y -= line_spacing
        pdf_canvas.setFont("Helvetica", 12)
        pdf_canvas.drawString(x, y, f"Project Name: {project_name}")
        y -= line_spacing
        pdf_canvas.drawString(x, y, f"Number of Slots Purchased: {quantity}")
        y -= line_spacing
        pdf_canvas.drawString(x, y, f"Cost Per Slot: ${cost_per_slot}")
        y -= line_spacing
        pdf_canvas.drawString(x, y, f"Total Amount: ${total_amount}")
        y -= line_spacing * 2

        # Payment Instructions
        pdf_canvas.setFont("Helvetica-Bold", 12)
        pdf_canvas.drawString(x, y, "PAYMENT INSTRUCTIONS:")
        y -= line_spacing
        pdf_canvas.setFont("Helvetica", 12)
        pdf_canvas.drawString(x, y, "Bank Name: Commerzbank")
        y -= line_spacing
        pdf_canvas.drawString(x, y, "Account Name: Realvista GmbH")
        y -= line_spacing
        pdf_canvas.drawString(x, y, "IBAN: DE06 XXXXX XXXXX XXXXX")
        y -= line_spacing
        pdf_canvas.drawString(
            x, y, f"Reference: {user_name or 'Invoice 001234'}")
        y -= line_spacing * 2

        # Notes
        pdf_canvas.setFont("Helvetica-Bold", 12)
        pdf_canvas.drawString(x, y, "NOTES:")
        y -= line_spacing
        pdf_canvas.setFont("Helvetica", 12)
        pdf_canvas.drawString(
            x, y, "- Please ensure payment is made within 7 business days.")
        y -= line_spacing
        pdf_canvas.drawString(
            x, y, "- Bank transfers may take up to 2 working days to process.")
        y -= line_spacing * 2

        # Footer
        pdf_canvas.setFont("Helvetica", 12)
        pdf_canvas.drawString(x, y, "Thank you for trusting Realvista GmbH!")

        # Finalize and save the PDF
        pdf_canvas.save()
        buffer.seek(0)

        # Create email
        subject = f"Invoice for Your Interest in the Project: {project_name}"
        message = (
            f"Dear {user_name},\n\n"
            f"Thank you for your interest in our project, {project_name}. We are delighted to assist you in completing your payment process.\n\n"
            "Please find attached a PDF invoice with all the necessary payment details. Kindly download and print the invoice for your records. "
            "You can proceed to make the payment via bank transfer using the details provided in the invoice.\n\n"
            "Note: Payments made through bank transfer may take up to two working days for verification.\n\n"
            "If you have any questions or need further assistance, feel free to reach out to us at support@example.com.\n\n"
            "Thank you for choosing Realvista GmbH. We look forward to serving you.\n\n"
            "Warm regards,\n"
            "Realvista Team"
        )
        email = EmailMessage(
            subject,
            message,
            "noreply@realvistaproperties.com",
            [user_email],
        )

        # Attach the PDF
        email.attach(f"Invoice_{project_name}.pdf",
                     buffer.getvalue(), "application/pdf")

        # Send the email
        email.send()
        return {"success": True, "message": "Invoice sent successfully."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def place_order(user, project, quantity, total_amount):
    with transaction.atomic():

        ordered_slots = project.ordered_slots or 0
        available_slots = project.num_slots - ordered_slots

        if quantity > available_slots:
            raise ValueError(
                f"Only {available_slots} slots available for project {project.name}"
            )

        order, created = Order.objects.get_or_create(
            user=user,
            project=project,
            quantity=quantity,
            total_amount=total_amount
        )

        if not created:
            available_slots += order.quantity

        if quantity > available_slots:
            raise ValueError(
                f"Only {available_slots} slots available for project {project.name}"
            )

        order.quantity = quantity
        order.total_amount = total_amount
        order.save()

        project.ordered_slots = project.num_slots - available_slots + quantity
        project.save()

        return order


EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


def send_push_notification(title, message, data=None, device_tokens=None, group_id=None):
    # Ensure device_tokens is provided
    if not device_tokens:
        return JsonResponse({'error': 'Device tokens are required'}, status=400)

    # Handle device_tokens as a list
    if isinstance(device_tokens, str):
        device_tokens = [device_tokens]

    notifications = []

    # Prepare individual notifications
    for token in device_tokens:
        notification = {
            "to": token,
            "title": title,
            "body": message,
            "data": data or {},
        }
        if group_id:
            notification["android"] = {
                "group": group_id,
            }
        notifications.append(notification)

    # Add a single group summary notification if group_id is provided
    if group_id:
        group_summary_notification = {
            "to": group_id,
            "title": f"{len(device_tokens)} new messages in Group Chat",
            "body": message,
            "data": {
                "groupId": f"group-{group_id}",
                **(data or {}),
            },
            "android": {
                "channelId": "group-chat",
                "isGroupSummary": True,
                "priority": "high",
            },
        }
        notifications.append(group_summary_notification)

    try:
        # Send notifications
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = requests.post(
            EXPO_PUSH_URL, headers=headers, data=json.dumps(notifications)
        )
        response_data = response.json()
        if response.status_code == 200:
            return JsonResponse({
                'status': 'Notifications sent successfully',
                'response': response_data,
                'total_notifications': len(notifications),
                'tokens_sent': [n['to'] for n in notifications],
            }, status=200)
        else:
            return JsonResponse({
                'error': 'Failed to send notifications',
                'status_code': response.status_code,
                'details': response_data,
            }, status=500)
    except requests.RequestException as e:
        return JsonResponse({
            'error': 'An error occurred while sending notifications',
            'details': str(e),
        }, status=500)


def send_general_notification(title, message, data=None):
    # Retrieve all devices
    devices = Device.objects.all()

    if not devices.exists():
        return JsonResponse({'error': 'No devices found'}, status=404)

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }

    notifications = []

    # Prepare notifications for all devices
    for device in devices:
        if device.token:
            notification = {
                "to": device.token,
                "title": title,
                "body": message,
                "data": data or {},
            }
            notifications.append(notification)

    try:
        # Send notifications
        response = requests.post(
            EXPO_PUSH_URL, headers=headers, data=json.dumps(notifications)
        )
        if response.status_code == 200:
            return JsonResponse({
                'status': 'Notifications sent successfully',
                'total_notifications': len(notifications),
                'tokens_sent': [n['to'] for n in notifications],
            }, status=200)
        else:
            return JsonResponse({
                'error': 'Failed to send notifications',
                'details': response.text,
            }, status=500)
    except requests.RequestException as e:
        return JsonResponse({
            'error': 'An error occurred while sending notifications',
            'details': str(e),
        }, status=500)


def record_user_progress(user, module, score, total):

    user_progress, created = UserProgress.objects.get_or_create(
        user=user,
        module=module,
        defaults={
            'score': score,
            'total': total,
            'passed': score >= (total * 0.7),
            'date_completed': timezone.now() if score >= (total * 0.7) else None
        }
    )

    if not created:
        user_progress.score = score
        user_progress.total = total
        user_progress.passed = score >= (total * 0.7)
        if score >= (total * 0.7) and not user_progress.date_completed:
            user_progress.date_completed = timezone.now()
        user_progress.save()

    return user_progress


# Avoid reinitialization in case of autoreload or multiple threads
if not firebase_admin._apps:
    cred = credentials.Certificate(settings.FIREBASE_ADMIN_CREDENTIAL)
    firebase_admin.initialize_app(cred)
