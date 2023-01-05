from django.apps import AppConfig
import logging


class CatalogConfig(AppConfig):
    name = 'rsshistory'

    def ready(self):
        pass

        from .prjconfig import Configuration
        c = Configuration.get_object(str(CatalogConfig.name))
        
        text = "APP ready: {0}".format(CatalogConfig.name)
        from .models import PersistentInfo
        PersistentInfo.cleanup()
        p = PersistentInfo.create(text)
