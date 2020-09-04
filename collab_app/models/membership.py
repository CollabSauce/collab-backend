from django.db import models

from collab_app.mixins.models import BaseModel


class Membership(BaseModel):
    organization = models.ForeignKey(
        'collab_app.Organization',
        related_name='memberships',
        on_delete=models.PROTECT
    )
    user = models.ForeignKey(
        'collab_app.User',
        related_name='memberships',
        on_delete=models.PROTECT
    )

    is_admin = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['organization', 'user'], name='unique_membership')
        ]
