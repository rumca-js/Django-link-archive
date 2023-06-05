from .baseplugin import BasePlugin
import re


class BaseParsePlugin(BasePlugin):
    def __init__(self, source):
        super().__init__(source)

    def get_address(self):
        return self.source.get_domain()

    def is_link_valid(self, address):
        if not self.is_link_valid_domain(address):
            return False;

        if address.endswith(".html") or address.endswith(".htm"):
            search_pattern = self.source.get_domain()

            if re.search(search_pattern, address):
                return True
        return False
