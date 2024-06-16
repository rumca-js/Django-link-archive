import os
import re

from ..models import UserTags
from ..configuration import Configuration
from .sourcerssplugin import BaseRssPlugin
from ..pluginurl import UrlHandler
from ..controllers import BackgroundJobController

from ..webtools import ContentLinkParser, HtmlPage, DomainAwarePage


class RssParserPlugin(BaseRssPlugin):
    """
    - We read RSS
    - For each item in RSS we find internal links for this source
    - For each internal link, we read page, and try to add links from inside
    """

    PLUGIN_NAME = "RssParserPlugin"

    def __init__(self, source_id):
        super().__init__(source_id)

    def get_container_elements(self):
        for prop in super().get_container_elements():
            prop = self.get_all_container_properties(prop)
            yield prop

    def get_all_container_properties(self, prop):
        self.add_additional_found_urls(prop)

    def add_additional_found_urls(self, entry_props):
        links = self.get_additional_links(entry_props)

        for link in links:
            BackgroundJobController.link_add(link, source=self.get_source())

    def get_additional_links(self, entry_props):
        links = self.get_description_links(entry_props)
        links.update(self.get_page_links(entry_props))

        domains = set()
        for link in links:
            p = DomainAwarePage(link)
            domains.add(p.get_domain())

        links.update(domains)

        return links

    def get_page_links(self, entry_properties):
        url = entry_properties["link"]
        h = UrlHandler(url)
        contents = h.get_contents()

        result = set()
        if not contents:
            return result

        if contents:
            parser = ContentLinkParser(url, contents)
            links = set(parser.get_links())
            result.update(links)

        return result

    def get_description_links(self, entry_properties):
        url = entry_properties["link"]
        contents = self.get_description_contents(entry_properties)

        result = set()

        if contents:
            parser = ContentLinkParser(url, contents)
            links = set(parser.get_links())
            result.update(links)

        return result

    def get_description_contents(self, properties):
        if "description" in properties:
            return properties["description"]

    def get_parser_links(parser):
        links = []
        c = Configuration.get_object().conf_entry
        if c.accept_domains:
            links.extend(parser.get_domains())

        if c.accept_not_domain_entries:
            links.extend(parser.get_links())
        return links

    def find_links_in_site(self, url):
        u = UrlHandler(url)
        p = ContentLinkParser(url, u.get_contents())
        return set(self.get_parser_links(p))
