import traceback
from dateutil import parser
from bs4 import BeautifulSoup

from webtoolkit import RssPage, RssContentReader

from ..webtools import (
    HttpPageHandler,
    YouTubeChannelHandler,
)

from ..models import AppLogging
from ..apps import LinkDatabase
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

    def get_container_reader_element(self):
        contents = self.get_contents()

        if not contents:
            return

        if not isinstance(contents, str):
            AppLogging.error("Contents is not string {}".format(contents))
            return

        # we could check if content-type suggests it is a RSS page
        # but server might say it is text/html (which is not)
        # This plugin handles RssPages

        reader = RssPage(self.get_address(), contents)
        if not reader.is_valid():
            content_reader = RssContentReader(self.get_address(), contents)
            if content_reader.contents:
                reader = RssPage(self.get_address(), content_reader.contents)
                if not reader.is_valid():
                    return
            else:
                return

        return reader

    def get_entries(self):
        """
        We override RSS behavior
        """

        remote_entries = 0
        for item in self.get_entries_standard():
            yield item
            remote_entries += 1

        if remote_entries > 0:
            return True

        for item in self.get_entries_manual():
            yield item

    def get_entries_manual(self):
        self.reader = self.get_container_reader_element()

        source = self.get_source()

        if not self.reader:
            AppLogging.error("Url:{}. Cannot read elements".format(source.url))
            return

        if source:
            source.update_data(update_with=self.reader)

        all_props = self.reader.get_entries()

        total_entries = 0

        for index, prop in enumerate(all_props):
            if not self.is_link_ok_to_add(prop):
                AppLogging.error(
                    "Page:{}. Cannot add link".format(self.get_address(), prop),
                    stack=True,
                )
                continue

            yield prop
            total_entries += 1

        if total_entries == 0:
            contents = self.get_contents()
            if contents:
                AppLogging.error(
                    "Url:{}. No links for rss".format(source.url), detail_text=contents
                )
            else:
                AppLogging.error(
                    "Url:{}. No links for rss, not contents".format(source.url)
                )

    def get_entries_standard(self):
        for data in super().get_entries():
            yield data
