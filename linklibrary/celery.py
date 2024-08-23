"""
This file should be updated to fit needs of your own project.

Provides means:
  - how to configure basic setup for threads
  - for more apps more code needs to be written (depends on your project)
"""

import os
from contextlib import contextmanager

from django.core.cache import cache

from celery import Celery
from celery.utils.log import get_task_logger
import importlib.util


# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "linklibrary.settings")

app = Celery("linklibrary")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


logger = get_task_logger(__name__)


LOCK_EXPIRE = 60 * 60 * 60  # Lock should never expire


@contextmanager
def memcache_lock(lock_id, oid):
    """!
    Memory cache lock

    @see
    https://docs.djangoproject.com/en/4.2/topics/cache/
    https://docs.djangoproject.com/en/4.2/ref/settings/
    https://docs.celeryq.dev/en/stable/tutorials/task-cookbook.html#cookbook-task-serial
    https://bobbyhadz.com/blog/operational-error-database-is-locked

    Note: This requires memcached to be configured in djanog
    https://stackoverflow.com/questions/53950548/flask-celery-task-locking
    """
    status = cache.add(lock_id, oid, LOCK_EXPIRE)
    try:
        yield status
    finally:
        if status:
            cache.delete(lock_id)


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """
    SQLite with Django does not like many tasks.
    If you plan use SQLite do not use this treading solution
    """
    cache.clear()

    # define for which apps support celery
    apps = [ "rsshistory", ]

    for app in apps:
        # periodic task names should be unique, new app tasks should not replace
        # the other task names
        # https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html

        tasks_module = importlib.import_module(app + ".tasks", package=None)
        tasks = tasks_module.get_tasks()

        # in seconds
        for task_info in tasks:
            time_s = task_info[0]
            task_processor = task_info[1]

            sender.add_periodic_task(
                time_s,
                process_all_jobs.s(app + ".threadhandlers." + str(task_processor)),
                name=app + " " + processor + " task ",
            )


@app.task(bind=True)
def process_all_jobs(self, processor):
    lock_id = "{0}-lock".format(self.name)
    with memcache_lock(lock_id, self.app.oid) as acquired:
        logger.info("Lock on:%s acquired:%s", self.name, acquired)
        if acquired:
            app = processor.split(".")[0]
            processor_file_name = processor.split(".")[1]
            processor_class_name = processor.split(".")[2]

            tasks_module = importlib.import_module(app + ".tasks", package=None)
            threadhandlers_module = importlib.import_module(app + ".threadhandlers", package=None)

            processor_class = getattr(threadhandlers_module, processor_class_name)

            tasks_module.process_jobs_task(processor_class)
