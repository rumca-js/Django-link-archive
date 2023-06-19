import re
from .baseparseplugin import BaseParsePlugin


class NiezaleznaPlugin(BaseParsePlugin):
    PLUGIN_NAME = "NiezaleznaPlugin"

    def __init__(self, source):
        super().__init__(source)

    def is_link_valid(self, address):
        if not self.is_link_valid_domain(address):
            return False;

        search_pattern = self.get_domain() + "/[0-9]+[-]"

        if re.search(search_pattern, address):
            return True
        return False
