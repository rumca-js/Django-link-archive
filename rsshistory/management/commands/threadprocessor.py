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
