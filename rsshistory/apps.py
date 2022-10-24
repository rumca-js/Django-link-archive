from django.apps import AppConfig
import logging


class CatalogConfig(AppConfig):
    name = 'rsshistory'

    def ready(self):
        from .prjconfig import Configuration
        c = Configuration.get_object(CatalogConfig.name)
        log = logging.getLogger(CatalogConfig.name)
        log.info("APP ready: {0}".format(CatalogConfig.name))
