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
import threading
import traceback

from django.core.management.base import BaseCommand
from django.conf import settings

from workspace import get_workspaces


def process_workspace(workspace, processor_class_name, processors_list, thread_name, check_memory):
    """
    Return more_jobs, errors indications
    """
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
    except TypeError as e:
        print("Processor class not found: ", str(e), processor_class_name)
        return

    # Call the task with the processor class
    try:
        return threadprocessors_module.process_job_task(Processor=processor_class,
                                                        processors_list=processors_list,
                                                        thread_name=thread_name,
                                                        check_memory=check_memory)
    except Exception as e:
        print("Error while processing jobs for: ", str(e), processor_class)
        error_text = traceback.format_exc()
        print(error_text)


class Command(BaseCommand):
    help = "Runs a background worker indefinitely"

    def add_arguments(self, parser):
        parser.add_argument("--process", type=str, help="Process name") # refresh
        parser.add_argument("--thread", type=str, help="Thread in process") # read1, etc.
        parser.add_argument("--workspace", type=str, help="Workspace") # read1, etc.

    def handle(self, *args, **options):
        thread = options["thread"]
        process = options["process"]
        input_workspace = options["workspace"]

        self.handle_threaded(input_workspace, process, thread)

    def handle_single_thread(self, process, thread):
        print(f"{process}/{thread}: Starting...")

        iteration = 1
        check_memory = False

        while True:
            # Do background work
            print(f"{process}/{thread}: Refresh")

            iteration += 1
            if iteration > 5:
                check_memory = True

            more_jobs = False
            errors = False

            for workspace in settings.WORKSPACES:
                more_jobs_workspace, errors_workspace = handle_workspace(workspace,
                                                                         thread,
                                                                         process,
                                                                         check_memory)
                if more_jobs_workspace:
                    more_jobs = True

                if errors_workspace:
                    errors = True

            if not more_jobs:
                print(f"{workspace}/{process}/{thread}: Waiting")
                time.sleep(10)  # 10 sec

            if errors:
                print(f"{workspace}/{process}/{thread}: Leaving because of errors")
                break

    def handle_workspace_single_thread(self, workspace, thread, process, check_memory):
        errors_workspace = True

        things = process_workspace(
             workspace=workspace,
             processor_class_name=process,
             processors_list=settings.PROCESSORS_INFO,
             thread_name=thread,
             check_memory=check_memory,
        )

        if things and len(things) > 1:
            more_jobs_workspace = things[0]
            errors_workspace = things[1]
        else:
            more_jobs_workspace = False
            print(f"{workspace}/{process}/{thread}: No thread return data")

        return more_jobs_workspace, errors_workspace

    def handle_threaded(self, input_workspace, process, thread):
        print(f"{process}/{thread}: Starting...")

        threads = []

        for workspace in settings.WORKSPACES:
            if input_workspace is not None and input_workspace != workspace:
                continue

            print(f"{process}/{thread}: Creating thread for {workspace}...")
            thread_id = threading.Thread(
                    target=self.handle_workspace_threaded,
                    args=(workspace, process, thread),
                    daemon=True,
            )
            thread_id.start()
            threads.append(thread_id)

        print(f"{process}/{thread}: Waiting for threads to complete...")
        for thread_id in threads:
            thread_id.join()

    def handle_workspace_threaded(self, workspace, process, thread):
        iteration = 0
        check_memory = False

        while True:
            print(f"{workspace}/{process}/{thread}: Start")

            #iteration += 1
            #if iteration > 10:
            #    check_memory = True

            more_jobs = False
            errors = False

            more_jobs_workspace, errors_workspace = self.handle_workspace_single_thread(workspace,
                                                                     thread,
                                                                     process,
                                                                     check_memory)
            if not more_jobs_workspace:
                time.sleep(30)  # 30 sec
            else:
                print(f"{workspace}/{process}/{thread}: More jobs to do")

            if errors_workspace:
                print(f"{workspace}/{process}/{thread}: Leaving because of errors")
                break

