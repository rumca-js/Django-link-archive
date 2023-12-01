import os
import time
from contextlib import contextmanager
from hashlib import md5

from celery import Celery

from django.core.cache import cache


# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'linklibrary.settings')

app = Celery('linklibrary')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)



LOCK_EXPIRE = 60 * 60  # Lock expires in 60 minutes

timeouts = {}

@contextmanager
def memcache_lock(lock_id, oid):
    """! 
    Memory cache lock

    @see
    https://docs.celeryq.dev/en/stable/tutorials/task-cookbook.html#cookbook-task-serial
    
    Note: This requires memcached to be configured in djanog
    https://stackoverflow.com/questions/53950548/flask-celery-task-locking
    """
    #if lock_id not in timeouts:
    #    timeouts[lock_id] = time.time()

    #timeout_at = time.monotonic() + LOCK_EXPIRE - 3
    # cache.add fails if the key already exists
    #status = cache.add(lock_id, oid, LOCK_EXPIRE)

    # https://docs.djangoproject.com/en/4.2/topics/cache/
    # https://docs.djangoproject.com/en/4.2/ref/settings/
    # using default timeout, most probably 5 seconds
    status = cache.add(lock_id, oid)
    try:
        #if status:
        #    del timeouts[lock_id]

        yield status
    finally:
        # memcache delete is very slow, but we have to use it to take
        # advantage of using add() for atomic locking
        # if time.monotonic() < timeout_at and status:
        if status:
            # don't release the lock if we exceeded the timeout
            # to lessen the chance of releasing an expired lock
            # owned by someone else
            # also don't release the lock if we didn't acquire it
            cache.delete(lock_id)
            #del timeouts[lock_id]


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # in seconds
    sender.add_periodic_task(300.0, rsshistory_main_checker_task.s('hello'), name='rsshistory Checker task')
    sender.add_periodic_task(60.0, rsshistory_main_process_all_jobs_task.s('hello'), name='rsshistory Processing task')



@app.task(bind=True)
def rsshistory_main_checker_task(self, arg):
    lock_id = '{0}-lock'.format(self.name)
    with memcache_lock(lock_id, self.app.oid) as acquired:
        logger.info('Lock on:%s acquired:%s', self.name, acquired)
        if acquired:
            from rsshistory.tasks import subs_checker_task as rsshistory_subs_checker_task
            rsshistory_subs_checker_task(arg)


@app.task(bind=True)
def rsshistory_main_process_all_jobs_task(self, arg):
    lock_id = '{0}-lock'.format(self.name)
    with memcache_lock(lock_id, self.app.oid) as acquired:
        logger.info('Lock on:%s acquired:%s', self.name, acquired)
        if acquired:
            from rsshistory.tasks import process_all_jobs_task as rsshistory_process_all_jobs_task
            rsshistory_process_all_jobs_task(arg)
