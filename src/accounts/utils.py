from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from rest_framework.response import Response
from rest_framework import status


def send_password_change_email(user):
    email_subject = "Your Password was Changed"

    # Render the email template
    html_content = render_to_string("emails/password_change_notification.html", {
        "user_name": user.name,
    })

    text_content = strip_tags(html_content)

    email_message = EmailMultiAlternatives(
        subject=email_subject,
        body=text_content,
        from_email='Realvista Properties <noreply@realvistaproperties.com>',
        to=[user.email]
    )
    email_message.attach_alternative(html_content, "text/html")
    email_message.send()
