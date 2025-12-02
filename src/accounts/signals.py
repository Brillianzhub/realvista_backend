from .models import User, Profile, UserPreference
from agents.models import Agent
from django.db.models.signals import post_save
from django.dispatch import receiver


# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         profile_data = {}

#         if hasattr(instance, 'agent_profile'):
#             agent = instance.agent_profile
#             profile_data.update({
#                 'avatar': agent.avatar,
#                 'phone_number': agent.phone_number,
#                 'whatsapp_number': agent.whatsapp_number,
#             })

#         Profile.objects.create(user=instance, **profile_data)


# @receiver(post_save, sender=User)
# def create_or_update_user_profile(sender, instance, created, **kwargs):
#     if created:
#         Profile.objects.create(user=instance)
#     else:
#         instance.profile.save()


@receiver(post_save, sender=User)
def create_or_update_user_preference(sender, instance, created, **kwargs):
    if created:
        UserPreference.objects.create(user=instance)
    else:
        instance.preferences.save()
