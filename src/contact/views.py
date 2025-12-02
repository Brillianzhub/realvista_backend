from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.conf import settings
import json
from .models import ContactMessage


@csrf_exempt
@require_POST
def submit_contact_message(request):
    try:
        data = json.loads(request.body)

        fullname = data.get('fullname')
        email = data.get('email')
        phone_number = data.get('phone_number')
        message = data.get('message')

        # Basic validation
        if not fullname or not email or not message:
            return JsonResponse({'error': 'Fullname, email, and message are required.'}, status=400)

        # Save to DB
        contact = ContactMessage.objects.create(
            fullname=fullname,
            email=email,
            phone_number=phone_number,
            message=message
        )

        # Send notification email
        subject = f"New Contact Message from {fullname}"
        body = (
            f"You have received a new contact message:\n\n"
            f"Full Name: {fullname}\n"
            f"Email: {email}\n"
            f"Phone Number: {phone_number}\n\n"
            f"Message:\n{message}"
        )
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            ['contact@realvistaproperties.com'],
            fail_silently=False
        )

        return JsonResponse({'success': 'Message submitted successfully.'}, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
