from django.conf import settings
from django.db import models

from collab_app.mixins.models import BaseModel


class Comment(BaseModel):
    thread = models.ForeignKey(
        'collab_app.Thread',
        related_name='comments',
        on_delete=models.CASCADE
    )
    bodytext = models.TextField()
    is_styling = models.BooleanField(default=False)

    def __str__(self):
        return self.bodytext


