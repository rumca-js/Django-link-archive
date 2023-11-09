import os
import re

from .sourceparseplugin import BaseParsePlugin


class SourceGenerousParserPlugin(BaseParsePlugin):
    PLUGIN_NAME = "SourceGenerousParserPlugin"

    def __init__(self, source_id):
        super().__init__(source_id)

    def is_link_valid(self, address):
        if not self.is_link_valid_domain(address):
            return False

        split = os.path.splitext(address)

        if split[1] == ".html" or split[1] == ".htm" or split[1] == "":
            print(address)
            return True
        else:
            return False
