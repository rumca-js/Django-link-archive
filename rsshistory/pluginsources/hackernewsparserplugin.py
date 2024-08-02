import os
import re

from ..models import UserTags
from ..configuration import Configuration
from .sourcerssplugin import BaseRssPlugin
from ..controllers import BackgroundJobController

from ..webtools import ContentLinkParser, HtmlPage, DomainAwarePage


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

        for prop in props:
            yield prop

        self.add_all_container_properties_to_queue(props)

    def add_all_container_properties_to_queue(self, props):
        for prop in props:
            self.add_additional_links_to_queue(prop)

    def add_additional_links_to_queue(self, entry_props):
        new_props = []

        self.get_container_element_links(entry_props)

    def get_container_element_links(self, entry_properties):
        contents = self.get_container_element_contents(entry_properties)

        if contents:
            parser = ContentLinkParser(contents)
            links = parser.get_links()

            for link in links:
                if link.find("news.ycombinator.com") >= 0:
                    BackgroundJobController.link_scan(link, source=self.get_source())

    def get_container_element_contents(self, properties):
        if "description" in properties:
            return properties["description"]
