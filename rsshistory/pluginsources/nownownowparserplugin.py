import os
import re

from ..models import LinkTagsDataModel
from .domainparserplugin import DomainParserPlugin


class NowNowNowParserPlugin(DomainParserPlugin):
    """
    Created for https://nownownow.com/
    """
    PLUGIN_NAME = "NowNowNowParserPlugin"

    def __init__(self, source_id):
        super().__init__(source_id)

    def on_added_entry(self, entry):
        from ..configuration import Configuration
        c = Configuration.get_object()

        LinkTagsDataModel.set_tag(entry, "personal", c.get_context()["admin_user"])
