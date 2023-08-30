from celery import shared_task
from celery.utils.log import get_task_logger

from linklibrary.celery import app, logger


def subs_checker_task(arg):
    """!
    Checks for new entries in sources
    """
    logger.info("Refreshing sources")

    from .threadhandlers import RefreshThreadHandler

    handler = RefreshThreadHandler()
    handler.refresh()

    logger.info("Refreshing sources done")


def process_all_jobs_task(arg):
    """!
    Processes jobs
    """
    logger.info("Processing source")

    from .threadhandlers import HandlerManager

    mgr = HandlerManager()
    mgr.process_all()

    logger.info("Processing done")
