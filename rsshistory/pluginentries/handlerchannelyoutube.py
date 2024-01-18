from .defaulturlhandler import DefaultUrlHandler
from ..webtools import RssPage


class YouTubeChannelHandler(DefaultUrlHandler):
    def __init__(self, url=None):
        super().__init__(url)

        if url:
            self.code = self.input2code(url)
            if self.code:
                self.h = RssPage(self.get_channel_feed())
            else:
                self.h = None

    def input2url(self, item):
        code = self.input2code(item)
        return self.code2url(code)

    def code2url(self, code):
        return "https://www.youtube.com/channel/{}".format(code)

    def code2feed(self, code):
        return "https://www.youtube.com/feeds/videos.xml?channel_id={}".format(code)

    def input2code(self, url):
        wh = url.find("www.youtube.com")
        if wh == -1:
            return url

        if url.find("/channel/") >= 0:
            return self.input2code_channel(url)
        if url.find("/feeds/") >= 0:
            return self.input2code_feeds(url)

    def input2code_channel(self, url):
        wh = url.rfind("/")
        return url[wh + 1 :]

    def input2code_feeds(self, url):
        wh = url.find("=")
        if wh >= 0:
            return url[wh + 1 :]

    def get_channel_code(self):
        return self.code

    def get_channel_url(self):
        return self.code2url(self.code)

    def get_channel_feed(self):
        return self.code2feed(self.code)

    def get_title(self):
        if self.h:
            return self.h.get_title()

    def get_description(self):
        if self.h:
            return self.h.get_description()

    def get_date_published(self):
        if self.h:
            return self.h.get_date_published()

    def get_language(self):
        if self.h:
            return self.h.get_language()

    def get_thumbnail(self):
        if self.h:
            return self.h.get_thumbnail()

    def get_author(self):
        if self.h:
            return self.h.get_author()

    def get_album(self):
        if self.h:
            return self.h.get_album()

    def get_tags(self):
        if self.h:
            return self.h.get_tags()
