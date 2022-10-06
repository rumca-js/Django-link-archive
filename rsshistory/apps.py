from django.apps import AppConfig
import logging


class CatalogConfig(AppConfig):
    name = 'rsshistory'

    def ready(self):
        print("Ready")
        from .prjconfig import Configuration
        c = Configuration.get_object()
        logging.info("APP ready: rsshistory")
