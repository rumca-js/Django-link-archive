from ..controllers import EntryDataBuilder, SourceDataController

class SourcePluginInterface(object):
    """
    Class names schemes:
     - those that are ancestors, and generic use "Base" class prefix
     - file names start with source, because I did not know if they will not be in one place
       with entries, so I wanted to be able to distinguish them later
    """
    PLUGIN_NAME = ""

    def __init__(self, source_id, options=None):
        self.source_id = source_id
        self.contents = None
        self.content_handler = None
        self.response = None
        self.dead = False

        self.get_source()

        self.hash = None

    def check_for_data(self):
        pass

    def get_entries(self):
        return []

    def get_source(self):
        sources = SourceDataController.objects.filter(id=self.source_id)
        if sources.exists():
            return sources[0]
