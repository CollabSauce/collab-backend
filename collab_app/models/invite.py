from django.db import models

from collab_app.mixins.models import BaseModel


class Invite(BaseModel):
    class InviteState(models.IntegerChoices):
        CREATED = 1
        ACCEPTED = 2
        DENIED = 3
        CANCELED = 4

    inviter = models.ForeignKey(
        'collab_app.User',
        related_name='invites_sent',
        on_delete=models.PROTECT
    )
    organization = models.ForeignKey(
        'collab_app.Organization',
        related_name='invites',
        on_delete=models.PROTECT
    )

    email = models.EmailField(unique=True)
    state = models.PositiveSmallIntegerField(choices=InviteState.choices, default=InviteState.CREATED)
    key = models.CharField(max_length=64, unique=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['organization', 'email', 'state'], name='unique_invite')
        ]
