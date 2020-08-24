from django.conf import settings
from django.db import models

from collab_app.mixins.models import BaseModel


class Profile(BaseModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
