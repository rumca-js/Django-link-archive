from django.apps import AppConfig


class CatalogConfig(AppConfig):
    name = 'rsshistory'

    def ready(self):
        pass
        from .prjconfig import Configuration
        c = Configuration.get_object()

    def __del__(self):
        from .prjconfig import Configuration
        c = Configuration.get_object() 
        c.close()
