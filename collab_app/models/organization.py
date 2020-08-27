from django.db import models

from collab_app.mixins.models import BaseModel


class Organization(BaseModel):
    name = models.TextField()
    key = models.CharField(max_length=32, unique=True)

    def __str__(self):
        return f'{self.name}'
