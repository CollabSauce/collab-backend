from django.db.models.signals import post_save
from django.dispatch import receiver

from collab_app.tasks import (
    notify_participants_of_task,
    notify_participants_of_task_comment,
    notify_participants_of_assignee_change
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


@receiver(post_save, sender='collab_app.Task')
def notify_on_task_assignment_change(sender, instance, created, **kwargs):
    task_id = instance.id  # readability
    assignee_diff = instance.get_field_diff('assigned_to')
    if not created and assignee_diff is not None:
        original_assignee_id, new_assignee_id = assignee_diff
        if new_assignee_id is not None:
            # TODO: notify original_assignee (if there was one) that they are unassigned??
            notify_participants_of_assignee_change.delay(task_id)
