
import traceback
from dateutil import parser
from bs4 import BeautifulSoup

from ..models import PersistentInfo
from ..apps import LinkDatabase
from ..webtools import RssPage, Url
from ..configuration import Configuration

from ..pluginentries.entryurlinterface import EntryUrlInterface
from ..pluginentries.entryurlinterface import UrlHandler

from .sourcerssplugin import BaseRssPlugin


class YouTubePlugin(BaseRssPlugin):
    PLUGIN_NAME = "YouTubeChannelPlugin"

    def __init__(self, source_id):
        super().__init__(source_id)

    def get_contents(self):
        if self.contents:
            return self.contents

        if self.dead:
            return

        from ..pluginentries.handlerchannelyoutube import YouTubeChannelHandler

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
    def get_contents(self):
        from ..programwrappers import ytdlp
        from ..pluginentries.handlerchannelyoutube import YouTubeChannelHandler

        source = self.get_source()
        channel = YouTubeChannelHandler(source.url)

        ytdlp = ytdlp.YTDLP(channel.get_channel_url())

        self.files = ytdlp.get_channel_video_list(newest=True)[:self.get_newest_limit()]
        self.contents = "\n".join(self.files)

    def get_link_props(self):
        contents = self.get_contents()

        for alink in self.files:
            LinkDatabase.info("Found YouTube file: {}".format(alink))
            entry_properties = self.get_clean_page_info(alink)

            yield entry_properties

    def get_clean_page_info(self, link):
        i = EntryUrlInterface(link)
        new_props = i.get_props()
        if not new_props:
            return prop

        for key in new_props:
            if new_props[key] is not None:
                prop[key] = new_props[key]
        return prop

    def get_newest_limit(self):
        return 15
    """
