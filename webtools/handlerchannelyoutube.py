import traceback

from .defaulturlhandler import DefaultChannelHandler
from .webtools import PageResponseObject
from .pages import RssPage
from .handlerhttppage import HttpPageHandler


class YouTubeChannelHandler(DefaultChannelHandler):
    """
    Natively since we inherit RssPage, the contents should be RssPage
    """

    def __init__(self, url=None, contents=None, page_options=None):
        self.html_url = None  # channel html page contains useful info
        self.rss_url = None

        super().__init__(
            url,
            contents=contents,
            page_options=page_options,
        )

        if url:
            self.code = self.input2code(url)

    def is_handled_by(self):
        from .url import Url

        if not self.url:
            return False

        short_url = Url.get_protololless(self.url)

        if (
            short_url.startswith("www.youtube.com/channel")
            or short_url.startswith("youtube.com/channel")
            or short_url.startswith("m.youtube.com/channel")
            or short_url.startswith("www.youtube.com/@")
            or short_url.startswith("youtube.com/@")
            or short_url.startswith("www.youtube.com/user")
            or short_url.startswith("youtube.com/user")
        ):
            return True
        if (
            short_url.startswith("www.youtube.com/feeds")
            or short_url.startswith("youtube.com/feeds")
            or short_url.startswith("m.youtube.com/feeds")
        ):
            return True

    def is_channel_name(self):
        from .url import Url

        if not self.url:
            return False

        short_url = Url.get_protololless(self.url)

        if (
            short_url.startswith("www.youtube.com/@")
            or short_url.startswith("youtube.com/@")
            or short_url.startswith("www.youtube.com/user")
            or short_url.startswith("youtube.com/user")
        ):
            return True

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

        if self.is_channel_name():
            return self.input2code_handle(url)
        if url.find("www.youtube.com/user") >= 0:
            return self.input2code_handle(url)
        if url.find("/channel/") >= 0:
            return self.input2code_channel(url)
        if url.find("/feeds/") >= 0:
            return self.input2code_feeds(url)

    def input2code_handle(self, url):
        html_page = self.get_html_page()

        if html_page:
            return html_page.get_schema_field("identifier")

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

    def get_feeds(self):
        result = []
        if self.code:
            result.append(self.code2feed(self.code))

        elif self.is_channel_name():
            html = self.get_html_page()
            if html:
                result.append(html.get_rss_url())

        return result

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
        from .url import Url
        from .webtools import WebLogger

        if self.response:
            return self.response

        if self.dead:
            return

        rss_url = self.get_rss_url()
        if rss_url:
            self.response = rss_url.get_response()

        if (
            not self.response
            or self.response.status_code == PageResponseObject.STATUS_CODE_ERROR
        ):
            self.dead = True

        if self.response:
            self.contents = self.response.get_text()
            return self.response

    def get_rss_url(self):
        from .url import Url
        from .webtools import WebLogger

        if self.rss_url:
            return self.rss_url

        feeds = self.get_feeds()
        if not feeds or len(feeds) == 0:
            WebLogger.error(
                "Url:{} Cannot read YouTube channel feed URL".format(self.url)
            )
            self.dead = True
            return

        feed = feeds[0]

        options = Url.get_url_options(feed)
        self.rss_url = Url(
            feed, page_options=options, handler_class=HttpPageHandler
        )
        return self.rss_url

    def get_html_url(self):
        from .url import Url

        if self.html_url:
            return self.html_url

        options = Url.get_url_options(self.url)

        u = Url(self.url, page_options=options, handler_class=HttpPageHandler)
        u.get_response()
        self.html_url = u

        if self.html_url:
            return self.html_url

    def get_html_page(self):
        html_url = self.get_html_url()
        if html_url:
            handler = html_url.get_handler()
            if handler.p:
                return handler.p

    def get_entries(self):
        rss_url = self.get_rss_url()
        if rss_url:
            return rss_url.get_entries()
        else:
            return []

    def get_title(self):
        rss_url = self.get_rss_url()
        if rss_url:
            return rss_url.get_title()

    def get_description(self):
        rss_url = self.get_rss_url()
        if rss_url:
            return rss_url.get_description()

    def get_language(self):
        rss_url = self.get_rss_url()
        if rss_url:
            return rss_url.get_language()

    def get_thumbnail(self):
        rss_url = self.get_rss_url()
        if rss_url:
            thumbnail = rss_url.get_thumbnail()
            if thumbnail:
                return thumbnail

        html_page = self.get_html_page()

        if html_page:
            return html_page.get_thumbnail()

    def get_author(self):
        rss_url = self.get_rss_url()
        if rss_url:
            return rss_url.get_author()

    def get_album(self):
        rss_url = self.get_rss_url()
        if rss_url:
            return rss_url.get_album()

    def get_tags(self):
        rss_url = self.get_rss_url()
        if rss_url:
            return rss_url.get_tags()
