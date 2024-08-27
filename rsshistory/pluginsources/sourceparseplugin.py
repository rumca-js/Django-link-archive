import traceback
import re
import os
import time

from webtools import DomainAwarePage, HtmlPage
from utils.dateutils import DateUtils

from ..models import AppLogging
from ..controllers import LinkDataController, BackgroundJobController
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

        # if not DomainAwarePage(self.get_address()).is_link_in_domain(address):
        #    return False

        # if not address.startswith(source.url):
        #    return False

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

    def get_entries(self):
        links_str_vec = self.get_links()
        num_entries = len(links_str_vec)

        for index, link_str in enumerate(links_str_vec):
            if not self.is_link_valid(link_str):
                continue

            objs = LinkDataController.objects.filter(link=link_str)
            if objs.exists():
                continue

            self.add_link(link_str)

        return []

    def calculate_plugin_hash(self):
        """
        We do not care about RSS title changing. We care only about entries
        Generic handler uses Html as base. We need to use RSS for body hash
        """

        # this is stupid to write get contents to have contents, to pass it it
        # to html page
        contents = self.get_contents()
        if not contents:
            return

        url = self.get_address()

        p = HtmlPage(url, contents)
        if p.is_valid:
            return p.get_contents_body_hash()
        else:
            return self.get_contents_hash()
