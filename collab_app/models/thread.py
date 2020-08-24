from django.conf import settings
from django.db import models
from django.db.models import Q

from collab_app.mixins.models import BaseModel


class Thread(BaseModel):

    organization = models.ForeignKey(
        'collab_app.Organization',
        related_name='threads',
        on_delete=models.CASCADE
    )

    target_id = models.TextField(blank=True)
    target_dom_path = models.TextField(blank=True)
    is_resolves = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_target_id_or_dom_path",
                check=(~Q(target_id='') | ~Q(target_dom_path=''))
            )
        ]


    def __str__(self):
        return self.bodytext


