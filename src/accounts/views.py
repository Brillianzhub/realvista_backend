from django.utils.http import urlsafe_base64_decode
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.shortcuts import render
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse

User = get_user_model()


def register_user(request):
    # Assume this is a POST request and email, password are sent as POST data
    email = request.POST['email']
    password = request.POST['password']
    user = User.objects.create_user(email=email, password=password)
    user.is_active = False  # Deactivate until email is verified
    user.save()
    send_verification_email(user)
    return render(request, 'registration/confirmation.html')


def send_verification_email(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    verification_url = f"{settings.DOMAIN}{reverse('verify_email')}?uid={uid}"
    subject = 'Verify your email address'
    message = f'Click the link to verify your email: {verification_url}'
    send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])


def verify_email(request):
    uid = request.GET.get('uid')
    user_id = urlsafe_base64_decode(uid).decode()
    user = User.objects.get(pk=user_id)
    if user:
        user.is_active = True
        user.save()
        return redirect('login')  # or a success page
    return render(request, 'registration/invalid_verification.html')
