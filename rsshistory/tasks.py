import traceback

from .apps import LinkDatabase
from .models import AppLogging
from .configuration import Configuration, ConfigurationEntry
from .threadhandlers import (
    GenericJobsProcessor,
    SourceJobsProcessor,
    WriteJobsProcessor,
    ImportJobsProcessor,
    LeftOverJobsProcessor,
)

from .threadhandlers import RefreshProcessor


def process_jobs_task(Processor):
    """!
    Checks for new entries in sources
    """
    logger = LinkDatabase

    logger.info("Starting process_jobs_task for processor: %s", Processor)

    try:
        c = Configuration.get_object()
        if not c.config_entry.background_tasks:
            logger.info("Background tasks are disabled in the configuration.")
            return

        c.config_entry = ConfigurationEntry.get()

        handler = Processor()
        handler.run()
    except Exception as E:
        logger.error("Exception in process_jobs_task for processor: %s", Processor, exc_info=True)
        AppLogging.exc(e, f"Exception in process_jobs_task {Processor}")

    logger.info("Finished process_jobs_task for processor: %s", Processor)


def get_processors():
    """
    Each processor will have each own dedicated queue.
    Write block will not affect source processing.
    """
    return [
        # if you are bottlenecked by resources,
        # you can leave only leftover processor
        # less queues, less CPU overhead
        SourceJobsProcessor,
        WriteJobsProcessor,
        ImportJobsProcessor,
        LeftOverJobsProcessor,
    ]


def get_tasks():
    tasks = [[300.0, RefreshProcessor]]
    processors = get_processors()

    for processor in processors:
        tasks.append([60.0, processor])

    return tasks
