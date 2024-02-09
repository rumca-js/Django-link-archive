from ..pluginurl.urlhandler import UrlHandler
from ..pluginurl.handlervideoyoutube import YouTubeVideoHandler
from ..webtools import RssPage, HtmlPage

from .fakeinternet import FakeInternetTestCase


class UrlHandlerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_get_rss(self):
        handler = UrlHandler.get("https://rsspage.com/rss.xml")

        self.assertTrue(handler.is_rss())
        self.assertEqual(type(handler), RssPage)

    def test_get_html(self):
        handler = UrlHandler.get("https://linkedin.com")

        self.assertTrue(handler.is_html())
        self.assertEqual(type(handler), HtmlPage)

    def test_get_youtube_video(self):
        handler = UrlHandler.get("https://www.youtube.com/watch?v=1234")

        self.assertEqual(type(handler), UrlHandler.youtube_video_handler)

    def test_get_youtube_channel(self):
        handler = UrlHandler.get(
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"
        )

        self.assertEqual(type(handler), UrlHandler.youtube_channel_handler)

    def test_rss_get_properties(self):
        handler = UrlHandler.get("https://simple-rss-page.com/rss.xml")

        props = handler.get_properties()

        self.assertEqual(props["title"], "Simple title")
        self.assertEqual(props["description"], "Simple description")

    def test_html_get_properties(self):
        handler = UrlHandler.get("https://linkedin.com")

        props = handler.get_properties()

        self.assertEqual(props["title"], "LinkedIn Page title")
        self.assertEqual(props["description"], "LinkedIn Page description")

    def test_youtube_channel_get_properties(self):
        handler = UrlHandler.get(
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"
        )

        props = handler.get_properties()

        self.assertEqual(props["title"], "SAMTIME on Odysee")

    def test_youtube_channel_get_title(self):
        handler = UrlHandler.get(
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"
        )

        self.assertEqual(handler.get_title(), "SAMTIME on Odysee")

    def test_get_spotify(self):
        handler = UrlHandler.get("https://open.spotify.com/somebody/episodes")

        self.assertEqual(type(handler), HtmlPage)

        self.assertTrue(handler.options.use_selenium_headless)

    def test_get_warhammer_community(self):
        handler = UrlHandler.get("https://www.warhammer-community.com")

        self.assertEqual(type(handler), HtmlPage)

        self.assertTrue(handler.options.use_selenium_full)

    def test_get__defcon_org(self):
        handler = UrlHandler.get("https://defcon.org")

        self.assertEqual(type(handler), HtmlPage)

        self.assertTrue(handler.options.use_selenium_full)
