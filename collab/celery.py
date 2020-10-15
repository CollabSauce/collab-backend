from __future__ import absolute_import
import os
from django.db import transaction

from celery import Celery, Task


# wrap in transaction.on_commit. see below links:
# https://browniebroke.com/blog/making-celery-work-nicely-with-django-transactions/
# https://docs.celeryproject.org/en/latest/userguide/tasks.html?highlight=on_commit#database-transactions
class TransactionAwareTask(Task):
    def delay_on_commit(self, *args, **kwargs):
        return transaction.on_commit(
            lambda: self.delay(*args, **kwargs)
        )


# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'collab.settings')
app = Celery('collab', task_cls=TransactionAwareTask)

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
