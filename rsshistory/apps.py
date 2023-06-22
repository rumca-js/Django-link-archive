from django.apps import AppConfig
import logging


class RssHistoryConfig(AppConfig):
    name = "rsshistory"
    verbose_name = "Personal link database"

    def ready(self):
        pass
