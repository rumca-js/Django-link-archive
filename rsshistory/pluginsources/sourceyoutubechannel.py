import traceback
from dateutil import parser
from bs4 import BeautifulSoup

from ..webtools import RssPage, Url

from ..apps import LinkDatabase
from ..configuration import Configuration

from .sourcerssplugin import BaseRssPlugin


class YouTubePlugin(BaseRssPlugin):
    PLUGIN_NAME = "YouTubeChannelPlugin"

    def __init__(self, source_id):
        super().__init__(source_id)

    def get_contents_from_rsshub(self):
        if self.contents:
            return self.contents

        if self.dead:
            return

        # TODO replace with builder?
        from ..pluginurl.handlerchannelyoutube import YouTubeChannelHandler

        source = self.get_source()
        channel = YouTubeChannelHandler(source.url)

        rss_page = "https://rsshub.app/youtube/channel/{}".format(channel.code)

        p = RssPage(rss_page)
        contents = p.get_contents()

        if not contents:
            self.dead = True
        else:
            self.contents = contents

        return self.contents

    """
    This plugin can be used, if youtube RSS feeds do not work

    def get_contents(self):
        return self.get_contents_from_rsshub()
    """
