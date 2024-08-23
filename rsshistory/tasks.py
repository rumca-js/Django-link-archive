import traceback

from .apps import LinkDatabase
from .models import AppLogging
from .configuration import Configuration
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
    LinkDatabase.info("process_jobs_task")

    try:
        c = Configuration.get_object()
        if not c.config_entry.background_tasks:
            return

        c.config_entry = ConfigurationEntry.get()

        handler = Processor()
        handler.run()
    except Exception as E:
        AppLogging.exc(E, "Exception in processor task")

    LinkDatabase.info("process_jobs_task DONE")


def get_processors():
    """
    Each processor will have each own dedicated queue.
    Write block will not affect source processing.
    """
    return [
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
