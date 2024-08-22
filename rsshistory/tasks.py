from celery import shared_task
from celery.utils.log import get_task_logger
import traceback

from linklibrary.celery import app, logger
from .apps import LinkDatabase
from .models import AppLogging
from .configuration import Configuration
from .threadhandlers import (
    GenericJobsProcessor,
    SourceJobsProcessor,
    WriteJobsProcessor,
    ImportJobsProcessor,
)

from .threadhandlers import RefreshThreadHandler


def jobs_checker_task(arg):
    """!
    Checks for new entries in sources
    """
    LinkDatabase.info("subs_checker_task")

    try:
        c = Configuration.get_object()
        if not c.config_entry.background_tasks:
            return

        c.config_entry = ConfigurationEntry.get()

        handler = RefreshThreadHandler()
        handler.refresh()
    except Exception as E:
        AppLogging.exc(E, "Exception in checker task")

    LinkDatabase.info("subs_checker_task DONE")


def process_jobs_task(Processor):
    """!
    Checks for new entries in sources
    """
    LinkDatabase.info("process_jobs_task")

    try:
        c = Configuration.get_object()
        if not c.config_entry.background_tasks:
            return

        c.config_entry = ConfigurationEntry.get()

        handler = Processor()
        handler.process_all()
    except Exception as E:
        AppLogging.exc(E, "Exception in processor task")

    LinkDatabase.info("process_jobs_task DONE")
