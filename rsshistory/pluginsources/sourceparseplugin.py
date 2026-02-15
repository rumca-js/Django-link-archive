import traceback
import re
import os
import time

from utils.dateutils import DateUtils
from webtoolkit import UrlLocation

from ..models import AppLogging
from ..controllers import LinkDataController, BackgroundJobController
from ..apps import LinkDatabase
from ..pluginurl.entryurlinterface import EntryUrlInterface
from ..configuration import Configuration

from .sourcegenericplugin import SourceGenericPlugin


class BaseParsePlugin(SourceGenericPlugin):
    PLUGIN_NAME = "BaseParsePlugin"

    def __init__(self, source_id):
        super().__init__(source_id)

    def get_link_data(self, source, link):
        url = EntryUrlInterface(link)

        props = url.get_props()
        if props:
            props["source_url"] = source.url
            props["source"] = source

        return props

    def get_entries(self):
        links_str_vec = self.get_links()
        num_entries = len(links_str_vec)

        for index, link_str in enumerate(links_str_vec):
            if not self.is_link_ok_to_add(link_str):
                continue

            objs = LinkDataController.objects.filter(link=link_str)
            if objs.exists():
                continue

            self.add_link(link_str)

        return []
