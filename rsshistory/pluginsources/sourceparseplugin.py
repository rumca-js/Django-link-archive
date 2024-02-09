import traceback
import re
import os
import time

from ..webtools import BasePage, HtmlPage, PageOptions
from ..dateutils import DateUtils
from ..models import PersistentInfo
from ..controllers import LinkDataController
from ..apps import LinkDatabase
from ..pluginurl.urlhandler import UrlHandler
from ..pluginurl.entryurlinterface import EntryUrlInterface
from ..configuration import Configuration

from .sourcegenericplugin import SourceGenericPlugin


class BaseParsePlugin(SourceGenericPlugin):
    PLUGIN_NAME = "BaseParsePlugin"

    def __init__(self, source_id):
        super().__init__(source_id)
        self.options = UrlHandler.get_page_options(self.get_address())

    def is_link_valid(self, address):
        source = self.get_source()

        if not self.is_link_valid_domain(address):
            return False

        if not address.startswith(source.url):
            return False

        p = BasePage(address)
        ext = p.get_page_ext()

        if ext == "html" or ext == "htm" or ext == None:
            return True

        return False

    def get_link_data(self, source, link):
        url = EntryUrlInterface(link)

        props = url.get_props()
        if props:
            props["source"] = source.url
            props["source_obj"] = source

        return props

    def get_links(self):
        result = []

        c = Configuration.get_object().config_entry
        if not c.auto_store_entries and c.auto_store_domain_info:
            result = self.get_domains()
        elif c.auto_store_entries:
            result = super().get_links()

        return result

    def get_container_elements(self):
        start_processing_time = time.time()

        links_str_vec = self.get_links()
        num_entries = len(links_str_vec)

        for index, link_str in enumerate(links_str_vec):
            if not self.is_link_valid(link_str):
                continue

            objs = LinkDataController.objects.filter(link=link_str)
            if objs.exists():
                continue

            link_props = self.get_link_data(self.get_source(), link_str)

            if not link_props or len(link_props) == 0:
                continue

            LinkDatabase.info(
                "Processing parsing link {}:[{}/{}]".format(
                    link_str, index, num_entries
                )
            )

            yield link_props

            # if 10 minutes passed
            if time.time() - start_processing_time >= 60 * 10:
                PersistentInfo.info("Spent too much time in parser")
                break
