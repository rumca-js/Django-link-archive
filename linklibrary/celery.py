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
import importlib
import logging
import time
import threading

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

LOCK_EXPIRE = 60 * 10  # 10 minutes lock expiration

@contextmanager
def memcache_lock(lock_id, oid):
    """
    Memcache-based locking mechanism with automatic expiration.

    Args:
        lock_id (str): The unique identifier for the lock.
        oid (str): The unique identifier for the task or worker trying to acquire the lock.

    Yields:
        bool: True if the lock was successfully acquired, False otherwise.
    """
    status = cache.add(lock_id, oid, LOCK_EXPIRE)
    
    def extend_lock():
        """ Function to periodically extend the lock """
        while status and cache.get(lock_id) == oid:
            time.sleep(LOCK_EXPIRE / 2)  # Sleep for half the lock expiration time
            cache.set(lock_id, oid, LOCK_EXPIRE)  # Extend the lock by resetting expiration
            logger.info(f"Lock {lock_id} extended for {LOCK_EXPIRE} seconds")

    # Start a background thread to extend the lock periodically
    if status:
        extension_thread = threading.Thread(target=extend_lock, daemon=True)
        extension_thread.start()

    try:
        yield status
    finally:
        if status and cache.get(lock_id) == oid:
            cache.delete(lock_id)
            logger.info(f"Lock {lock_id} released")


# define for which apps support celery
installed_apps = [ "rsshistory", ]


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """
    SQLite with Django does not like many tasks.
    If you plan use SQLite do not use this treading solution

    Cannot import apps.tasks
    """

    try:
        logger.info("Clearing cache")
        cache.clear()

        tasks_info = [
                [300.0, "RefreshProcessor"],
                [60.0, "SourceJobsProcessor"],
                [60.0, "WriteJobsProcessor"],
                [60.0, "ImportJobsProcessor"],
                [60.0, "LeftOverJobsProcessor"],
        ]

        for app in installed_apps:
            for task_info in tasks_info:
                time_s = task_info[0]
                task_processor = task_info[1]

                logger.info("Tasks. {} Adding {} {}".format(app, time_s, task_processor))

                sender.add_periodic_task(
                    time_s,
                    process_all_jobs.s(app + ".threadprocessors." + task_processor),
                    name=app + " " + task_processor + " task",
                )

                logger.info("Tasks. {} Adding {} {} DONE".format(app, time_s, task_processor))

        logger.info("Defined all tasks successfully")
    except Exception as E:
        logger.error("Processor class not found: %s", str(E))



@app.task(bind=True)
def process_all_jobs(self, processor):
    """
    Ensures that the same app/processor doesn't run concurrently.
    Uses a memcache-based lock to prevent duplicate runs.
    """
    lock_id = "{}{}-lock".format(self.name, processor)

    # Using a context manager to acquire a lock
    with memcache_lock(lock_id, self.app.oid) as acquired:
        try:
            logger.info("Attempting to acquire lock for: %s", processor)
            
            if acquired:
                logger.info("Lock acquired for: %s", processor)

                app_name = None
                processor_file_name = None
                processor_class_name = None
                processor_class = None
                tasks_module = None
                threadprocessors_module = None

                # Parsing the processor string
                try:
                    app_name, processor_file_name, processor_class_name = processor.split(".")
                except ValueError as e:
                    logger.error("Processor string format error: %s", processor, exc_info=True)
                    return

                # Importing tasks and processor modules
                try:
                    tasks_module = importlib.import_module(f"{app_name}.tasks")
                    threadprocessors_module = importlib.import_module(f"{app_name}.threadprocessors")
                except ModuleNotFoundError as e:
                    logger.error("Module import failed for app: %s", app_name, exc_info=True)
                    return
                
                # Retrieving the processor class
                try:
                    processor_class = getattr(threadprocessors_module, processor_class_name)
                except AttributeError as e:
                    logger.error("Processor class not found: %s", processor_class_name, exc_info=True)
                    return

                # Call the task with the processor class
                try:
                    tasks_module.process_jobs_task(processor_class)
                    logger.info("Task processed successfully for: %s", processor)
                except Exception as e:
                    logger.error("Error while processing jobs for: %s", processor, exc_info=True)

            else:
                logger.info("Lock not acquired for: %s, another task is already running.", processor)

        except Exception as e:
            logger.error("Unexpected error occurred in process_all_jobs: %s", processor, exc_info=True)
