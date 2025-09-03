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
from django.core.management.base import BaseCommand
from django.conf import settings
import time
from workspace import get_workspaces, process_app


class Command(BaseCommand):
    help = 'Runs a background worker indefinitely'

    def add_arguments(self, parser):
        parser.add_argument('--thread', type=str, help='Thread name')


    def handle(self, *args, **options):
        thread = options["thread"]

        while True:
            # Do background work
            print(f"Doing work...{thread}")

            for workspace in get_workspaces():
                process_app(f"{workspace}.threadprocessors.{thread}", settings.TASKS_INFO)

            time.sleep(10)
