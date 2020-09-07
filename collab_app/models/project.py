from django.db import models

from collab_app.mixins.models import BaseModel


class Project(BaseModel):
    name = models.TextField()
    key = models.CharField(max_length=32, unique=True)
    url = models.TextField(blank=True, default='')  # make this a url field? Does it even matter?

    organization = models.ForeignKey(
        'collab_app.Organization',
        related_name='projects',
        on_delete=models.PROTECT
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['organization', 'name'], name='unique_project_org')
        ]

    def __str__(self):
        return f'{self.name}'
