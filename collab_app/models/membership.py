from django.db import models

from collab_app.mixins.models import BaseModel


class Membership(BaseModel):
    class RoleType(models.IntegerChoices):
        ADMIN = 1
        DASHBOARD = 2
        WIDGET = 3

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

    role = models.PositiveSmallIntegerField(choices=RoleType.choices, default=RoleType.DASHBOARD)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['organization', 'user'], name='unique_membership')
        ]
