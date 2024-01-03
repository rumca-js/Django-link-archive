from django.apps import AppConfig


class LinkDatabase(AppConfig):
    name = "rsshistory"
    verbose_name = "Personal link database"

    def ready(self):
        pass

    def info(message):
        print("[{}] {}".format(LinkDatabase.name, message))

    def error(message):
        print("[{}] {}".format(LinkDatabase.name, message))
