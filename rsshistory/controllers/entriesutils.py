from django.db import models
from django.db.models import Q, F

from webtoolkit import RemoteServer, UrlLocation, ContentLinkParser

from ..configuration import Configuration
from ..apps import LinkDatabase
from .backgroundjob import BackgroundJobController


def add_all_domains(page_url):
    links = set()

    p = UrlLocation(page_url)
    domain = p.get_domain()

    links.add(domain)

    while True:
        p = p.up()
        if not p or p.get_domain() is None:
            break

        links.add(p.get_domain())

    for link in links:
        BackgroundJobController.link_add(link)


class EntryContentsCrawler(object):
    def __init__(self, link, contents, source=None):
        self.link = link
        self.contents = contents
        self.source = source

    def get_links(self):
        """
        Adds links from description of that link.
        Store link as-is.
        """
        config = Configuration.get_object().config_entry

        if config.enable_crawling:
            links = self.get_sanitized_links()
            return links

    def get_sanitized_links(self):
        result_links = set()
        links = self.get_crawl_links()
        for link in links:
            link = UrlLocation.get_cleaned_link(link)
            result_links.add(link)

        return links

    def get_crawl_links(self):
        links = set()

        parser = ContentLinkParser(
            self.link, self.contents
        )

        config = Configuration.get_object().config_entry

        if config.accept_non_domain_links:
            links = set(parser.get_links())

        if config.accept_domain_links:
            links = set(parser.get_domains())

            p = UrlLocation(self.link)
            domain = p.get_domain()
            if domain and domain != self.link:
                links.add(domain)

        links -= {self.link}

        return links


class EntryPageCrawler(object):
    def __init__(self, url=None, entry=None, properties=None):
        if url:
            self.url = url
        if entry:
            self.url = entry.link

        self.properties = properties
        self.entry = entry

    def run(self):
        c = Configuration.get_object()
        config = c.config_entry
        if not config.enable_crawling or not config.auto_scan_new_entries:
            return

        if self.entry:
            if self.entry.page_rating < 0:
                return

        contents = None
        description = None

        if self.properties:
            request_server = RemoteServer("https://")
            contents = request_server.read_properties_section("Contents", self.properties)
            props = request_server.read_properties_section("Properties", self.properties)
            description = props.get("description")
        else:
            from ..pluginurl import UrlHandlerEx
            handler = UrlHandlerEx(self.url)
            handler.get_response()
            contents = handler.get_contents()
            description = handler.get_description()

        source = None
        if self.entry:
            source = self.entry.source

        links = set()

        crawler = EntryContentsCrawler(self.url, description, source)
        links.update(crawler.get_links())

        crawler = EntryContentsCrawler(self.url, contents, source)
        links.update(crawler.get_links())

        for link in links:
            BackgroundJobController.link_add(link)
