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

    def info(message):
        print("[{}] {}".format(LinkDatabase.name, message))

    def error(message):
        print("[{}] {}".format(LinkDatabase.name, message))
