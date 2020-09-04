from django.db import models

from collab_app.mixins.models import BaseModel


class Organization(BaseModel):
    name = models.TextField()

    def __str__(self):
        return f'{self.name}'
