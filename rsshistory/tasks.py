import traceback

from .apps import LinkDatabase
from .models import AppLogging
from .configuration import Configuration, ConfigurationEntry


def process_jobs_task(Processor, tasks_info):
    """!
    Checks for new entries in sources
    """
    c = Configuration.get_object()
    if not c.config_entry.enable_background_jobs:
        return

    c.config_entry = ConfigurationEntry.get()

    handler = Processor(tasks_info=tasks_info)

    handler.run()
