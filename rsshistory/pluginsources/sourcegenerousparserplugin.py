import re
from .sourceparseplugin import BaseParsePlugin


class SourceGenerousParserPlugin(BaseParsePlugin):
    PLUGIN_NAME = "SourceGenerousParserPlugin"

    def __init__(self, source):
        super().__init__(source)

    def is_link_valid(self, address):
        if not self.is_link_valid_domain(address):
            return False

        if (
            address.endswith(".html")
            or address.endswith(".htm")
            or address.endswith("/")
        ):
            return True
        else:
            return False
