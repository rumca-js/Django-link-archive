from ..webtools import Url, PageOptions

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class UrlTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_get_favicon(self):
        MockRequestCounter.mock_page_requests = 0
        favicon = Url("https://multiple-favicons/page.html").get_favicon()

        self.assertEqual(
            favicon, "https://www.youtube.com/s/desktop/e4d15d2c/img/favicon.ico"
        )

        self.assertEqual(MockRequestCounter.mock_page_requests, 1)

    def test_get_for_page_spotify(self):
        MockRequestCounter.mock_page_requests = 0

        o = PageOptions()
        o.use_selenium_full = True
        handler = Url("https://open.spotify.com", page_options=o)

        self.assertEqual(handler.options.use_selenium_full, True)

        self.assertEqual(MockRequestCounter.mock_page_requests, 1)

    def test_get_for_page_youtube(self):
        MockRequestCounter.mock_page_requests = 0

        o = PageOptions()
        o.use_selenium_headless = True
        handler = Url("https://open.spotify.com", page_options=o)

        self.assertEqual(handler.options.use_selenium_headless, True)

        self.assertEqual(MockRequestCounter.mock_page_requests, 1)
