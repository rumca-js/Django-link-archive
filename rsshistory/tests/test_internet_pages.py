from ..pluginurl.urlhandler import UrlHandler
from ..pluginurl.handlervideoyoutube import YouTubeVideoHandler
from ..webtools import RssPage, HtmlPage, HttpPageHandler

from .fakeinternet import FakeInternetTestCase


class InternetTest(FakeInternetTestCase):
    """
    Handles all difficult pages, that have to be workaround with
    """

    def setUp(self):
        self.disable_web_pages()

    def test_rss_in_html(self):
        """
        Warhammer community could not be read because rss was in html, and
        because 'link' property was not set by feedparser package
        """
        handler = UrlHandler("https://warhammer-community.com/feed")
        handler.get_response()

        self.assertEqual(type(handler.get_handler()), HttpPageHandler)
        self.assertEqual(type(handler.get_handler().p), RssPage)

        container_elements = list(handler.get_handler().p.get_entries())

        self.assertTrue(len(container_elements) > 0)
        self.assertTrue(container_elements[0]["link"] != "")

    def test_the_hill_rss(self):
        """
        The hill could not be read because 'link' property was not set by feedparser package
        """
        handler = UrlHandler("https://warhammer-community.com/feed")
        handler.get_response()

        self.assertEqual(type(handler.get_handler()), HttpPageHandler)
        self.assertEqual(type(handler.get_handler().p), RssPage)

        container_elements = list(handler.get_handler().p.get_entries())

        self.assertTrue(len(container_elements) > 0)
        self.assertTrue(container_elements[0]["link"] != "")

    def test_youtube_channel(self):
        """
        YouTube channels are protected by cookie requests
        """
        handler = UrlHandler("https://www.youtube.com/user/linustechtips")
        handler.get_response()

        self.assertEqual(
            type(handler.get_handler()), UrlHandler.youtube_channel_handler
        )
        # self.assertEqual(type(handler.get_handler().handler), HtmlPage)

        props = handler.get_properties()

        elf.assertEqual(props["title"], "Linus Tech Tips")
