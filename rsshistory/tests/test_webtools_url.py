from ..webtools import Url, PageOptions

from .fakeinternet import FakeInternetTestCase


class UrlTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_get_favicon(self):
        favicon = Url.get_favicon("https://multiple-favicons/page.html")

        self.assertEqual(
            favicon, "https://www.youtube.com/s/desktop/e4d15d2c/img/favicon.ico"
        )

    def test_get_for_page_spotify(self):
        o = PageOptions()
        o.use_selenium_full = True
        handler = Url.get("https://open.spotify.com", options=o)

        self.assertEqual(handler.options.use_selenium_full, True)

    def test_get_for_page_youtube(self):
        o = PageOptions()
        o.use_selenium_headless = True
        handler = Url.get("https://open.spotify.com", options=o)

        self.assertEqual(handler.options.use_selenium_headless, True)
