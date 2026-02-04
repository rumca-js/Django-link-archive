import traceback
import gc

from .apps import LinkDatabase
from .models import AppLogging
from .configuration import Configuration, ConfigurationEntry


def process_jobs_task(Processor, tasks_info):
    """!
    Processes all jobs for task
    """
    c = Configuration.get_object()
    if not c.config_entry.enable_background_jobs:
        return

    c.config_entry = ConfigurationEntry.get()

    handler = Processor(tasks_info=tasks_info)

    handler.run()

    more_jobs = handler.is_more_jobs()
    errors = handler.is_error()
    gc.collect()
    return more_jobs, errors


def process_job_task(Processor, tasks_info):
    """!
    Processes on job for task
    """
    c = Configuration.get_object()
    if not c.config_entry.enable_background_jobs:
        return

    c.config_entry = ConfigurationEntry.get()

    handler = Processor(tasks_info=tasks_info)

    status = handler.run_one_job()
    more_jobs = handler.is_more_jobs()
    errors = handler.is_error()
    gc.collect()
    return more_jobs, errors
