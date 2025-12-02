from accounts.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import AgentVerification
from .utils.email import (
    send_verification_email,
    send_verification_submission_email,
)


@receiver(post_save, sender=AgentVerification)
def update_user_identity_verification(sender, instance, created, **kwargs):
    user = instance.agent.user

    if created:
        # Send submission received email
        send_verification_submission_email(user)

    elif instance.reviewed:
        if instance.approved:
            if not user.is_identity_verified:
                user.is_identity_verified = True
                user.save()
            send_verification_email(user, approved=True)
        else:
            send_verification_email(
                user, approved=False, reason=instance.rejection_reason)


@receiver(post_save, sender=AgentVerification)
def update_agent_verified_status(sender, instance, **kwargs):
    if instance.approved and not instance.agent.verified:
        instance.agent.verified = True
        instance.agent.save()


@receiver(post_save, sender=AgentVerification)
def update_user_identity_verification(sender, instance, **kwargs):
    user = instance.agent.user

    if instance.reviewed:
        if instance.approved:
            if not user.is_identity_verified:
                user.is_identity_verified = True
                user.save()
            send_verification_email(user, approved=True)
        else:
            send_verification_email(
                user, approved=False, reason=instance.rejection_reason)
