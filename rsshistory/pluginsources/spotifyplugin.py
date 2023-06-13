from .baseplugin import BasePlugin
import re


class SpotifyPlugin(BasePlugin):
    PLUGIN_NAME = "SpotifyPlugin"

    def __init__(self, source):
        super().__init__(source)

    def is_link_valid(self, address):
        if not self.is_link_valid_domain(address):
            return False;

        search_pattern = self.get_domain() + "/episode"

        if re.search(search_pattern, address):
            return True
        return False
