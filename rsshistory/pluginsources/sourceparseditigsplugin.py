import re
from .sourceparseplugin import BaseParsePlugin


class SourceParseDigitsPlugin(BaseParsePlugin):
    PLUGIN_NAME = "SourceParseDigitsPlugin"

    def __init__(self, source):
        super().__init__(source)

    def is_link_valid(self, address):
        """
        Allow only links with digits at start, after domain
        """
        if not self.is_link_valid_domain(address):
            return False

        search_pattern = self.get_domain() + "/[0-9]+"

        if re.search(search_pattern, address):
            return True
        return False