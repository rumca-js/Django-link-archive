import re
from .sourceparseplugin import BaseParsePlugin
from ..webtools import DomainAwarePage


class SourceParseDigitsPlugin(BaseParsePlugin):
    PLUGIN_NAME = "SourceParseDigitsPlugin"

    def __init__(self, source_id):
        super().__init__(source_id)

    def is_link_valid(self, address):
        """
        Allow only links with digits at start, after domain
        """
        if not DomainAwarePage(self.get_address()).is_link_in_domain(address):
            return False

        search_pattern = self.get_domain() + "/[0-9]+"

        if re.search(search_pattern, address):
            return True
        return False
