from .defaulturlhandler import DefaultUrlHandler
from ..webtools import RssPage, Url, PageResponseObject
from ..models import AppLogging


class YouTubeChannelHandler(RssPage, DefaultUrlHandler):
    def __init__(self, url=None, contents=None):
        super().__init__(
            url,
            contents=contents,
        )

        if url:
            self.code = self.input2code(url)

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

        if url.find("www.youtube.com/@") >= 0:
            return self.input2code_handle(url)
        if url.find("/channel/") >= 0:
            return self.input2code_channel(url)
        if url.find("/feeds/") >= 0:
            return self.input2code_feeds(url)

    def input2code_handle(self, url):
        pass
        # u = Url(url)
        # contents = u.get_contents()

    def input2code_channel(self, url):
        wh = url.rfind("/")
        return url[wh + 1 :]

    def input2code_feeds(self, url):
        wh = url.find("=")
        if wh >= 0:
            return url[wh + 1 :]

    def get_channel_code(self):
        return self.code

    def get_channel_name(self):
        return self.code

    def get_channel_url(self):
        return self.code2url(self.code)

    def get_channel_feed_url(self):
        return self.code2feed(self.code)

    def get_contents(self):
        """
        We obtain information about channel.
        We cannot use HTML page to obtain thumbnail - as web page asks to log in to view this
        """
        if self.dead:
            return

        response = self.get_response()
        if response:
            return self.response.get_contents()

    def get_response(self):
        if self.response:
            return self.response

        u = Url(self.get_channel_feed_url())
        self.response = u.get_response()

        if (
            not self.response
            or self.response.status_code == PageResponseObject.STATUS_CODE_ERROR
        ):
            self.dead = True

        if self.response:
            self.contents = self.response.get_contents()
            self.process_contents()

            return self.response
