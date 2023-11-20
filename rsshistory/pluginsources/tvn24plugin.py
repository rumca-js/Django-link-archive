from .sourcerssplugin import BaseRssPlugin


class TVN24Plugin(BaseRssPlugin):
    PLUGIN_NAME = "TVN24Plugin"

    def __init__(self, source_id):
        super().__init__(source_id)

    def is_link_valid(self, address):
        if address.find("TVN24-po-ukrainsku") >= 0:
            return False
        return True
