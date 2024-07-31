from .defaulturlhandler import DefaultUrlHandler
from ..webtools import RssPage, Url, PageResponseObject
from ..models import AppLogging


class YouTubeChannelHandler(RssPage, DefaultUrlHandler):
    """
    Natively since we inherit RssPage, the contents should be RssPage
    """
    def __init__(self, url=None, contents=None):
        super().__init__(
            url,
            contents=contents,
        )

        self.html_page = None # channel html page contains useful info

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
        if url.find("www.youtube.com/user") >= 0:
            return self.input2code_handle(url)
        if url.find("/channel/") >= 0:
            return self.input2code_channel(url)
        if url.find("/feeds/") >= 0:
            return self.input2code_feeds(url)

    def get_html_page(self, url):
        from .urlhandler import UrlHandler

        if self.html_page:
            return self.html_page

        options = UrlHandler.get_url_options(url)
        u = Url(url, page_options=options)
        u.get_response()
        self.html_page = u.handler.p
        return self.html_page

    def input2code_handle(self, url):
        if not self.html_page:
            self.get_html_page(url)

        if self.html_page:
            return self.html_page.get_schema_field("identifier")

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
        if self.code:
            return self.code2url(self.code)

    def get_channel_feed_url(self):
        if self.code:
            return self.code2feed(self.code)

    def get_contents(self):
        """
        We obtain information about channel.
        We cannot use HTML page to obtain thumbnail - as web page asks to log in to view this
        """
        if self.dead:
            return

        if self.contents:
            return self.contents

        response = self.get_response()
        if response:
            return self.response.get_text()

    def get_response(self):
        from .urlhandler import UrlHandler

        if self.response:
            return self.response

        feed_url = self.get_channel_feed_url()
        if not feed_url:
            AppLogging.error("Url:{} Cannot read YouTube channel feed URL".format(self.url))
            self.dead = True
            return

        options = UrlHandler.get_url_options(feed_url)
        u = Url(feed_url, page_options=options)
        self.response = u.get_response()

        if (
            not self.response
            or self.response.status_code == PageResponseObject.STATUS_CODE_ERROR
        ):
            self.dead = True

        if self.response:
            self.contents = self.response.get_text()
            self.process_contents()

            return self.response

    def get_thumbnail(self):
        if not self.html_page:
            channel_url = self.get_channel_url()
            if channel_url:
                self.get_html_page(channel_url)

        if self.html_page:
            return self.html_page.get_thumbnail()
