"""
I have tried some things for background processing:
 - background thread in app.py - it was clunky, and hacky
 - celery - requires memcache, rabbitmq or redis, so many things may go wrong
   had problems, occasional hiccups in transmission and I did not know why.
   I were debugging for a long period of time, and found nothing
   maybe memcache was cluttered with dued signals, maybe not. maybe there were other things
   I was running big long running tasks, and celery I think is not for that
 - this - I can clearly see threads - by name. Is much closer to what I wanted to achieve
"""

import time
import importlib
import traceback

from django.core.management.base import BaseCommand
from django.conf import settings

from workspace import get_workspaces


def process_workspace(workspace, processor_class_name, tasks_info, check_memory):
    # Importing tasks and processor modules
    try:
        threadprocessors_module = importlib.import_module(
            f"{workspace}.threadprocessors"
        )
    except ModuleNotFoundError as e:
        print("Module import failed for workspace: %s", workspace)
        return

    # Retrieving the processor class
    try:
        processor_class = getattr(threadprocessors_module, processor_class_name)
    except AttributeError as e:
        print("Processor class not found: ", str(e), processor_class_name)
        return

    # Call the task with the processor class
    try:
        return threadprocessors_module.process_job_task(processor_class, tasks_info, check_memory)
    except Exception as e:
        print("Error while processing jobs for: ", str(e), processor_class)
        error_text = traceback.format_exc()
        print(error_text)


class Command(BaseCommand):
    help = "Runs a background worker indefinitely"

    def add_arguments(self, parser):
        parser.add_argument("--thread", type=str, help="Thread name")

    def handle(self, *args, **options):
        thread = options["thread"]

        print(f"{thread}: Starting...")

        iteration = 1
        check_memory = False

        while True:
            # Do background work
            print(f"{thread}: Refresh")

            iteration += 1
            if iteration > 5:
                check_memory = True

            more_jobs = False

            for workspace in get_workspaces():
                more_jobs_now = process_workspace(
                     workspace,
                     thread,
                     settings.TASKS_INFO,
                     check_memory,
                )
                if more_jobs_now:
                    more_jobs = True

            if not more_jobs:
                print(f"{thread}: Waiting")
                time.sleep(10)  # 10 sec
