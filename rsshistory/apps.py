from django.apps import AppConfig
import logging


class RssHistoryConfig(AppConfig):
    name = 'rsshistory'

    def ready(self):
        pass

        #from .prjconfig import Configuration
        #c = Configuration.get_object(str(RssHistoryConfig.name))
        
        #text = "APP ready: {0}".format(RssHistoryConfig.name)
        #from .models import PersistentInfo
        #PersistentInfo.cleanup()
        #p = PersistentInfo.create(text)
        #print(text)
