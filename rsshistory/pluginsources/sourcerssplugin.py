import traceback
from dateutil import parser
from bs4 import BeautifulSoup

from ..webtools import RssPage, HttpPageHandler, YouTubeChannelHandler

from ..models import AppLogging
from ..apps import LinkDatabase
from ..pluginurl import UrlHandler
from ..configuration import Configuration

from .sourcegenericplugin import SourceGenericPlugin


class BaseRssPlugin(SourceGenericPlugin):
    """
    TODO this inherits HTML, not RSS
    """

    PLUGIN_NAME = "BaseRssPlugin"

    def __init__(self, source_id):
        super().__init__(source_id)
        source = self.get_source()

    def is_rss(self, handler):
        if type(handler) is YouTubeChannelHandler:
            return True

        if type(handler) is HttpPageHandler and handler.is_rss():
            return True

        return False

    def get_contents_size_limit(self):
        return 800

    def get_entries(self):
        """
        We override RSS behavior
        """
        c = Configuration.get_object().config_entry

        contents = self.get_contents()
        source = self.get_source()

        if not contents:
            return

        # we could check if content-type suggests it is a RSS page
        # but server might say it is text/html (which is not)
        # This plugin handles RssPages

        self.reader = RssPage(self.get_address(), contents)
        if not self.reader.is_valid():
            content_reader = RssContentReader(self.get_address(), contents)
            if content_reader.contents:
                self.reader = RssPage(self.get_address(), content_reader.contents)
            else:
                AppLogging.error("Url:{}. RSS page is not valid".format(source.url))
                return

        all_props = self.reader.get_entries()

        total_entries = 0

        for index, prop in enumerate(all_props):
            if not self.is_link_ok_to_add(prop):
                AppLogging.error(
                    "Page:{}. Cannot add link".format(self.get_address(), prop),
                    stack=True,
                )
                continue

            prop = self.enhance(prop)
            yield prop
            total_entries += 1

        if total_entries == 0:
            AppLogging.error("Url:{}. No links for rss".format(source.url))

    def enhance(self, prop):
        prop["link"] = UrlHandler.get_cleaned_link(prop["link"])

        source = self.get_source()

        if (
            self.is_property_set(prop, "language")
            and source.language != None
            and source.language != ""
        ):
            prop["language"] = source.language

        return prop
