import re

from webtools import DomainAwarePage

from .sourceparseplugin import BaseParsePlugin


class SpotifyPlugin(BaseParsePlugin):
    PLUGIN_NAME = "SpotifyPlugin"

    def __init__(self, source_id):
        super().__init__(source_id)

    def is_link_valid(self, address):
        url = self.get_address()

        if not DomainAwarePage(url).is_link_in_domain(address):
            return False

        search_pattern = DomainAwarePage(url).get_domain() + "/episode"

        if re.search(search_pattern, address):
            return True
        return False
