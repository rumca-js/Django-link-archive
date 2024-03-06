from celery import shared_task
from celery.utils.log import get_task_logger
import traceback

from linklibrary.celery import app, logger
from .apps import LinkDatabase
from .models import AppLogging


def subs_checker_task(arg):
    """!
    Checks for new entries in sources
    """
    LinkDatabase.info("subs_checker_task")

    try:
        from .configuration import Configuration

        #if not Configuration.get_object().config_entry.background_task:
        #    return

        from .threadhandlers import RefreshThreadHandler

        handler = RefreshThreadHandler()
        handler.refresh()
    except Exception as E:
        error_text = traceback.format_exc()
        AppLogging.error(
            "Exception in checker task: {} {}".format(str(E), error_text)
        )

    LinkDatabase.info("subs_checker_task DONE")


def process_all_jobs_task(arg):
    """!
    Processes jobs
    """
    LinkDatabase.info("process_all_jobs_task")

    try:
        from .configuration import Configuration

        #if not Configuration.get_object().config_entry.background_task:
        #    return

        from .threadhandlers import HandlerManager

        mgr = HandlerManager()
        return mgr.process_all()

    except Exception as E:
        error_text = traceback.format_exc()
        AppLogging.error(
            "Exception in processing task: {} {}".format(str(E), error_text)
        )

    LinkDatabase.info("process_all_jobs_task DONE")


def process_one_jobs_task(arg):
    """!
    Processes jobs
    """
    LinkDatabase.info("process_one_jobs_task")

    try:
        from .configuration import Configuration

        #if not Configuration.get_object().config_entry.background_task:
        #    return

        from .threadhandlers import HandlerManager

        mgr = HandlerManager()
        return mgr.process_one()

    except Exception as E:
        error_text = traceback.format_exc()
        AppLogging.error(
            "Exception in processing task: {} {}".format(str(E), error_text)
        )

    LinkDatabase.info("process_one_jobs_task DONE")
