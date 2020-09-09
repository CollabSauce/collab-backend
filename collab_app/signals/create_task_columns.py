from django.apps import apps
from django.db.models.signals import post_save
from django.dispatch import receiver


"""
Create the task columns for the project on create of a project.
"""


@receiver(post_save, sender='collab_app.Project')
def create_task_columns_on_project_create(sender, instance, created, **kwargs):

    project = instance

    if created:
        TaskColumn = apps.get_model('collab_app', 'TaskColumn')
        for name in TaskColumn.TASK_COLUMN_NAMES:
            TaskColumn.objects.create(
                name=name,
                project=project
            )

