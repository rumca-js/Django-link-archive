import traceback

from .apps import LinkDatabase
from .models import AppLogging
from .configuration import Configuration, ConfigurationEntry


def process_jobs_task(Processor):
    """!
    Checks for new entries in sources
    """
    logger = LinkDatabase

    logger.info("Starting process_jobs_task for processor: {}".format(Processor))

    try:
        c = Configuration.get_object()
        if not c.config_entry.background_tasks:
            logger.info("Background tasks are disabled in the configuration.")
            return

        c.config_entry = ConfigurationEntry.get()

        handler = Processor()
        handler.run()
    except Exception as E:
        logger.error(
            "Exception in process_jobs_task for processor: {} {}".format(
                Processor, str(E)
            )
        )
        AppLogging.exc(E, f"Exception in process_jobs_task {Processor}")

    logger.info("Finished process_jobs_task for processor: {}".format(Processor))
