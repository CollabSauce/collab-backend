from django.db import models
from django.db.models import Q

from collab_app.mixins.models import BaseModel


class Task(BaseModel):
    title = models.TextField(blank=True, default='')
    description = models.TextField(blank=True, default='')
    design_edits = models.TextField(blank=True, default='')
    window_screenshot_url = models.TextField(blank=True, default='')
    element_screenshot_url = models.TextField(blank=True, default='')
    task_number = models.PositiveIntegerField()
    is_resolved = models.BooleanField(default=False)
    target_id = models.TextField(blank=True, default='')
    target_dom_path = models.TextField(blank=True, default='')

    # for ordering inside a task_column
    order = models.PositiveIntegerField(default=0)

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
                name="%(app_label)s_%(class)s_title_or_design_edits",
                check=(~Q(title='') | ~Q(design_edits=''))
            ),
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_target_id_or_dom_path",
                check=(~Q(target_id='') | ~Q(target_dom_path=''))
            )
        ]

class TaskColumn(BaseModel):
    TASK_COLUMN_RAW_TASK = 'Raw Task'
    TASK_COLUMN_NAMES = [TASK_COLUMN_RAW_TASK, 'To-Do', 'In Progress', 'In Review', 'Done', 'Released']

    name = models.TextField()

    project = models.ForeignKey(
        'collab_app.Project',
        related_name='task_columns',
        on_delete=models.PROTECT
    )


class TaskMetadata(BaseModel):
    url_origin = models.TextField(default='')
    os_name = models.TextField(default='')
    os_version = models.TextField(default='')
    os_version_name = models.TextField(default='')
    browser_name = models.TextField(default='')
    browser_version = models.TextField(default='')
    selector = models.TextField(default='')
    screen_height = models.PositiveSmallIntegerField(default=0)
    screen_width = models.PositiveSmallIntegerField(default=0)
    device_pixel_ratio = models.PositiveSmallIntegerField(default=0)
    browser_window_width = models.PositiveSmallIntegerField(default=0)
    browser_window_height = models.PositiveSmallIntegerField(default=0)
    color_depth = models.PositiveSmallIntegerField(default=0)
    pixel_depth = models.PositiveSmallIntegerField(default=0)

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
