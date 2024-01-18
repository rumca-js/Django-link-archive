
from ..webtools import Url

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
        handler = Url.get("https://open.spotify.com")

        self.assertEqual(handler.use_selenium, True)

    def test_get_for_page_wsj(self):
        handler = Url.get("https://www.wsj.com")

        self.assertEqual(handler.use_selenium, True)

    def test_get_for_page_youtube(self):
        handler = Url.get("https://www.youtube.com")

        self.assertEqual(handler.use_selenium, False)
