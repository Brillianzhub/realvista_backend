from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


def send_verification_email(user, approved=True, reason=None):
    if approved:
        subject = "Identity Verification Approved"
        html_content = render_to_string("notifications/verification_approved.html", {
            "user": user,
        })
    else:
        subject = "Identity Verification Rejected"
        html_content = render_to_string("notifications/verification_rejected.html", {
            "user": user,
            "reason": reason,
        })

    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [user.email]

    msg = EmailMultiAlternatives(subject, '', from_email, to_email)
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def send_verification_submission_email(user):
    subject = "Verification Documents Received"
    html_content = render_to_string("notifications/verification_submitted.html", {
        "user": user,
    })

    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [user.email]

    msg = EmailMultiAlternatives(subject, '', from_email, to_email)
    msg.attach_alternative(html_content, "text/html")
    msg.send()
