from django.apps import AppConfig
import logging


class CatalogConfig(AppConfig):
    name = 'rsshistory'

    def ready(self):
        pass
        
        text = "APP ready: {0}".format(CatalogConfig.name)
        from .models import PersistentInfo
        PersistentInfo.cleanup()
        p = PersistentInfo.create(text)
