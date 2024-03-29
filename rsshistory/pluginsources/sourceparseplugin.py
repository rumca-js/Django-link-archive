import traceback
import re
import os
import time

from ..webtools import DomainAwarePage, HtmlPage, PageOptions
from ..dateutils import DateUtils
from ..models import AppLogging
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

    def is_link_valid(self, address):
        source = self.get_source()

        if not DomainAwarePage(self.get_address()).is_link_in_domain(address):
            return False

        if not address.startswith(source.url):
            return False

        p = DomainAwarePage(address)
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
                AppLogging.info("Spent too much time in parser")
                break

    def calculate_plugin_hash(self):
        """
        We do not care about RSS title changing. We care only about entries
        Generic handler uses Html as base. We need to use RSS for body hash
        """

        # this is stupid to write get contents to have contents, to pass it it
        # to html page
        contents = self.get_contents()
        url = self.get_address()

        print("Calculating plugin hash")
        p = HtmlPage(url, contents)
        if p.is_valid:
            print("Calculating plugin hash is html")
            return p.get_body_hash()
        else:
            return self.get_contents_hash()
