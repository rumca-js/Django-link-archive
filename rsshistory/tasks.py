import traceback

from .apps import LinkDatabase
from .models import AppLogging
from .configuration import Configuration, ConfigurationEntry


def process_jobs_task(Processor, tasks_info):
    """!
    Checks for new entries in sources
    """
    AppLogging.info("Starting process_jobs_task for processor: {}".format(Processor))

    try:
        c = Configuration.get_object()
        if not c.config_entry.enable_background_jobs:
            AppLogging.info("Background tasks are disabled in the configuration.")
            return

        c.config_entry = ConfigurationEntry.get()

        handler = Processor(tasks_info = tasks_info)
        handler.run()
    except Exception as E:
        AppLogging.error(
            "Exception in process_jobs_task for processor: {} {}".format(
                Processor, str(E)
            )
        )
        AppLogging.exc(E, f"Exception in process_jobs_task {Processor}")

    AppLogging.info("Finished process_jobs_task for processor: {}".format(Processor))
