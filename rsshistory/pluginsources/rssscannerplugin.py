import os
import re

from ..models import UserTags
from ..configuration import Configuration
from .sourcerssplugin import BaseRssPlugin

from ..webtools import ContentLinkParser, HtmlPage, BasePage


class RssScannerPlugin(BaseRssPlugin):
    """
     - We read RSS
     - For each item in RSS we find internal links for this source
     - For each internal link, we read page, and try to add links from inside
    """

    PLUGIN_NAME = "RssScannerPlugin"

    def __init__(self, source_id):
        super().__init__(source_id)

    def get_container_elements(self):
        props = super().get_container_elements()

        for prop in props:
            new_props = self.on_container_element(prop)
            for new_prop in new_props:
                props.append(new_prop)

        for prop in props:
            yield prop

    def on_container_element(self, props):
        new_props = []

        self.get_container_element_links(props)
        for container_link in links:
            if self.is_internal_page_processed(container_link):
                props = self.process_internal_page(container_link)

                new_props.extend(props)

        return new_props

    def get_container_element_contents(self, properties):
        if "description" in properties:
            return properties["description"]

    def get_container_element_links(self, properties):
        contents = self.get_container_element_contents(properties)

        if contents:
            parser = ContentLinkParser(contents)
            links = parser.get_links()
            return links
        else:
            return []

    def is_internal_page_processed(self, url):
        url_page = BasePage(url)
        source_page = BasePage(self.get_source().url)

        return url_page.get_domain() == source_page.get_domain()

    def process_internal_page(self, url):
        all_props = []

        p = HtmlPage(url)
        parser = ContentLinkParser(p.get_contents())

        for link in parser.get_links():
            i = UrlEntryInterface(link=link)
            props = i.get_props()
            all_props.append(props)

        return all_props
