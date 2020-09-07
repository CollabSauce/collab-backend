from django.apps import apps
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()

"""
Create a profile when a user is created.
"""


@receiver(post_save, sender=User)
def create_profile_on_user_create(sender, instance, created, **kwargs):

    user = instance

    if created:
        Profile = apps.get_model('collab_app', 'Profile')

        Profile.objects.create(user=user)
