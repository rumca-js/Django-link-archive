import os
import re

from ..webtools import Page
from .sourceparseplugin import BaseParsePlugin


class SourceGenerousParserPlugin(BaseParsePlugin):
    PLUGIN_NAME = "SourceGenerousParserPlugin"

    def __init__(self, source_id):
        super().__init__(source_id)

    def is_link_valid(self, address):
        if not self.is_link_valid_domain(address):
            return False

        p = Page(address)
        ext = p.get_page_ext()

        if ext == "html" or ext == "htm" or ext == "":
            return True
        else:
            return False
