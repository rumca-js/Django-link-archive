import os
import re

from ..webtools import DomainAwarePage
from .sourceparseplugin import BaseParsePlugin


class SourceParseInternalLinks(BaseParsePlugin):
    PLUGIN_NAME = "SourceParseInternalLinks"

    def __init__(self, source_id):
        super().__init__(source_id)

    def is_link_valid(self, address):
        if not super().is_link_valid(address):
            return False

        source_address = self.get_address()
        return DomainAwarePage(source_address).get_domain() == DomainAwarePage(address).get_domain()
