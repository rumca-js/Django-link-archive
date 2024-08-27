import re

from webtools import DomainAwarePage

from .sourceparseplugin import BaseParsePlugin


class SourceParseDigitsPlugin(BaseParsePlugin):
    PLUGIN_NAME = "SourceParseDigitsPlugin"

    def __init__(self, source_id):
        super().__init__(source_id)

    def is_link_valid(self, address):
        """
        Allow only links with digits at start, after domain
        """
        if not super().is_link_valid(address):
            return False

        search_pattern = self.get_domain() + "/[0-9]+"

        if re.search(search_pattern, address):
            return True
        return False
