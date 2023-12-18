from celery import shared_task
from celery.utils.log import get_task_logger
import traceback

from linklibrary.celery import app, logger
from .apps import LinkDatabase


def subs_checker_task(arg):
    """!
    Checks for new entries in sources
    """
    LinkDatabase.info("Refreshing sources")

    try:
        from .threadhandlers import RefreshThreadHandler

        handler = RefreshThreadHandler()
        handler.refresh()
    except Exception as E:
        error_text = traceback.format_exc()
        LinkDatabase.info("Exception in checker task: {} {}".format(str(E), error_text))

    LinkDatabase.info("Refreshing sources done")


def process_all_jobs_task(arg):
    """!
    Processes jobs
    """
    LinkDatabase.info("Processing source")

    try:
        from .threadhandlers import HandlerManager

        mgr = HandlerManager()
        return mgr.process_all()

    except Exception as E:
        error_text = traceback.format_exc()
        LinkDatabase.info(
            "Exception in processing task: {} {}".format(str(E), error_text)
        )

    LinkDatabase.info("Processing done")


def process_one_jobs_task(arg):
    """!
    Processes jobs
    """
    LinkDatabase.info("Processing source")

    try:
        from .threadhandlers import HandlerManager

        mgr = HandlerManager()
        return mgr.process_one()

    except Exception as E:
        error_text = traceback.format_exc()
        LinkDatabase.info(
            "Exception in processing task: {} {}".format(str(E), error_text)
        )

    LinkDatabase.info("Processing done")
