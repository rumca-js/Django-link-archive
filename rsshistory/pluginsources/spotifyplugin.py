from .sourceparseplugin import BaseParsePlugin
import re


class SpotifyPlugin(BaseParsePlugin):
    PLUGIN_NAME = "SpotifyPlugin"

    def __init__(self, source_id):
        super().__init__(source_id)

    def is_link_valid(self, address):
        if not self.is_link_valid_domain(address):
            return False

        search_pattern = self.get_domain() + "/episode"

        if re.search(search_pattern, address):
            return True
        return False
