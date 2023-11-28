import os
import re

from ..models import LinkTagsDataModel
from ..configuration import Configuration
from .sourcerssplugin import BaseRssPlugin


class SearchMySiteRSSPlugin(BaseRssPlugin):
    """
    Created for https://searmysite.net/
    """

    PLUGIN_NAME = "SearchMySiteRSSPlugin"

    def __init__(self, source_id):
        super().__init__(source_id)

    def on_added_entry(self, entry):
        c = Configuration.get_object()

        LinkTagsDataModel.set_tag(entry, "personal", c.get_context()["admin_user"])
