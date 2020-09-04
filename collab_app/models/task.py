from django.db import models
from django.db.models import Q

from collab_app.mixins.models import BaseModel


class Task(BaseModel):
    comment = models.TextField(blank=True, default='')
    design_edits = models.TextField(blank=True, default='')
    screenshot_url = models.TextField(null=True, blank=True)
    task_number = models.PositiveIntegerField()
    is_resolved = models.BooleanField(default=False)
    target_id = models.TextField(blank=True, default='')
    target_dom_path = models.TextField(blank=True, default='')

    project = models.ForeignKey(
        'collab_app.Project',
        related_name='tasks',
        on_delete=models.PROTECT
    )

    task_column = models.ForeignKey(
        'collab_app.TaskColumn',
        related_name='tasks',
        on_delete=models.PROTECT
    )

    creator = models.ForeignKey(
        'collab_app.User',
        related_name='created_tasks',
        on_delete=models.PROTECT
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['task_number', 'project'], name='unique_tasknumber_project'),
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_comment_or_design_edits",
                check=(~Q(comment='') | ~Q(design_edits=''))
            ),
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_target_id_or_dom_path",
                check=(~Q(target_id='') | ~Q(target_dom_path=''))
            )
        ]


class TaskColumn(BaseModel):
    name = models.TextField()


class TaskMetadata(BaseModel):
    task_logged_at = models.TextField(default='')
    operating_system = models.TextField(default='')
    browser = models.TextField(default='')
    selector = models.TextField(default='')
    resolution = models.TextField(default='')
    browser_window = models.TextField(default='')
    color_depth = models.TextField(default='')

    task = models.OneToOneField(
        'collab_app.Task',
        related_name='task_metadata',
        on_delete=models.PROTECT
    )


class TaskComment(BaseModel):
    task = models.ForeignKey(
        'collab_app.Task',
        related_name='task_comments',
        on_delete=models.PROTECT
    )
    text = models.TextField()

    creator = models.ForeignKey(
        'collab_app.User',
        related_name='created_task_comments',
        on_delete=models.PROTECT
    )
