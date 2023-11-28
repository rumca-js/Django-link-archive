from celery import shared_task
from celery.utils.log import get_task_logger
import traceback

from linklibrary.celery import app, logger


def subs_checker_task(arg):
    """!
    Checks for new entries in sources
    """
    logger.info("Refreshing sources")

    from .apps import LinkDatabase
    try:
        from .threadhandlers import RefreshThreadHandler

        handler = RefreshThreadHandler()
        handler.refresh()
    except Exception as E:
        error_text = traceback.format_exc()
        print("[{}] Exception in checker task: {} {}".format(LinkDatabase.name, str(E), error_text))

    logger.info("Refreshing sources done")


def process_all_jobs_task(arg):
    """!
    Processes jobs
    """
    logger.info("Processing source")

    from .apps import LinkDatabase
    try:
        from .threadhandlers import HandlerManager

        mgr = HandlerManager()
        mgr.process_all()

    except Exception as E:
        error_text = traceback.format_exc()
        print("[{}] Exception in processing task: {} {}".format(LinkDatabase.name, str(E), error_text))

    logger.info("Processing done")
