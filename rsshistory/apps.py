import atexit
from django.apps import AppConfig


def cleanup_on_exit():
    # Your cleanup code here
    # print("App Cleanup")
    pass


class LinkDatabase(AppConfig):
    name = "rsshistory"
    verbose_name = "Personal link database"

    def ready(self):
        # print("App Ready {}".format(LinkDatabase.name))
        atexit.register(cleanup_on_exit)

        try:
            from .models import SystemOperation
            SystemOperation.objects.all().delete()

            from .models import AppLogging
            from .dateutils import DateUtils
            from .configuration import Configuration

            c = Configuration.get_object()
            current_date = DateUtils.get_datetime_now_utc()
            current_date = c.get_local_time(current_date)

            AppLogging.notify("System is ready {}.".format(current_date))

        except Exception as E:
            # TODO this is stupid, that it prints errors during migrations
            print(str(E))
            print("Exception can occur, if this is first run of migrations. Do not worry.")

    def info(message):
        print("[{}] {}".format(LinkDatabase.name, message))

    def error(message):
        print("[{}] {}".format(LinkDatabase.name, message))
