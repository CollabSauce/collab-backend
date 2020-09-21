from django.db.models.signals import post_save
from django.dispatch import receiver

from collab_app.tasks import (
    notify_participants_of_task,
    notify_participants_of_task_comment
)


"""
Notify participants of task when a task or task comment is created.
"""


@receiver(post_save, sender='collab_app.Task')
def notify_on_task_create(sender, instance, created, **kwargs):
    task_id = instance.id  # readability
    if created:
        notify_participants_of_task.delay(task_id)


@receiver(post_save, sender='collab_app.TaskComment')
def notify_on_task_comment_create(sender, instance, created, **kwargs):
    task_comment_id = instance.id  # readability
    if created:
        notify_participants_of_task_comment.delay(task_comment_id)
