"""
This file should be updated to fit needs of your own project.

Provides means:
  - how to configure basic setup for threads
  - for more apps more code needs to be written (depends on your project)
"""

import os
import time
from contextlib import contextmanager
from hashlib import md5

from celery import Celery

from django.core.cache import cache


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

from celery.utils.log import get_task_logger

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
    cache.clear()

    # in seconds
    sender.add_periodic_task(
        300.0, jobs_checker_task.s("hello"), name="Jobs checker task"
    )
    sender.add_periodic_task(
        60.0,
        process_all_jobs.s("hello"),
        name="rsshistory Processing task",
    )


@app.task(bind=True)
def jobs_checker_task(self, arg):
    lock_id = "{0}-lock".format(self.name)
    with memcache_lock(lock_id, self.app.oid) as acquired:
        logger.info("Lock on:%s acquired:%s", self.name, acquired)
        if acquired:
            from rsshistory.tasks import (
                jobs_checker_task as rsshistory_jobs_checker_task,
            )

            rsshistory_jobs_checker_task(arg)


@app.task(bind=True)
def process_all_jobs(self, arg):
    lock_id = "{0}-lock".format(self.name)
    with memcache_lock(lock_id, self.app.oid) as acquired:
        logger.info("Lock on:%s acquired:%s", self.name, acquired)
        if acquired:
            from rsshistory.threadhandlers import GenericJobsProcessor
            from rsshistory.tasks import process_jobs_task

            # we could device jobs between various threads

            processors = [
                    #SourceJobsProcessor,
                    #WriteJobsProcessor,
                    #ImportJobsProcessor,
                    GenericJobsProcessor,]

            for processor in processors:
                process_jobs_task(processor)
