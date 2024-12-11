import os
import re

from ..webtools import ContentLinkParser

from ..models import UserTags
from ..configuration import Configuration
from .sourcerssplugin import BaseRssPlugin
from ..controllers import BackgroundJobController


class HackerNewsParserPlugin(BaseRssPlugin):
    """
    - We read RSS
    - For each item in RSS we find internal links for this source
    - For each internal link, we read page, and try to add links from inside
    """

    PLUGIN_NAME = "HackerNewsScannerPlugin"

    def __init__(self, source_id):
        super().__init__(source_id)

    def get_entries(self):
        props = super().get_entries()
        list_props = list(props)

        for prop in list_props:
            yield prop

        self.add_all_container_properties_to_queue(list_props)

    def add_all_container_properties_to_queue(self, props):
        for prop in props:
            self.add_additional_links_to_queue(prop)

    def add_additional_links_to_queue(self, entry_props):
        new_props = []

        self.get_container_element_links(entry_props)

    def get_container_element_links(self, entry_properties):
        url = None
        contents = None

        if entry_properties and "description" in entry_properties:
            contents = entry_properties["description"]
            url = entry_properties["link"]

        if contents and url:
            parser = ContentLinkParser(url, contents)
            links = parser.get_links()

            for link in links:
                if link.find("news.ycombinator.com") >= 0:
                    BackgroundJobController.link_scan(link, source=self.get_source())

    def get_container_element_contents(self, properties):
        if "description" in properties:
            return properties["description"]
