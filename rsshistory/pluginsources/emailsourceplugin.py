from .sourceplugininterface import SourcePluginInterface
from utils.services import EmailReader


class EmailSourcePlugin(SourcePluginInterface):
    """
    Class names schemes:
     - those that are ancestors, and generic use "Base" class prefix
     - file names start with source, because I did not know if they will not be in one place
       with entries, so I wanted to be able to distinguish them later
    """
    PLUGIN_NAME = "EmailSourcePlugin"

    def __init__(self, source_id, options=None):
        super().__init__(source_id=source_id, options=options)

    def check_for_data(self):
        pass

    def get_entries(self):
        return []
