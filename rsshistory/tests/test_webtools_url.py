from ..webtools import Url, PageOptions, HtmlPage, PageResponseObject

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class PageResponseObjectTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_get_content_type(self):
        headers = {"Content-Type": "text/html"}
        response = PageResponseObject(
            "https://test.com", "", status_code=200, headers=headers
        )

        # call tested function
        self.assertEqual(response.get_content_type(), "text/html")

    def test_is_valid__true(self):
        headers = {"Content-Type": "text/html"}

        response = PageResponseObject(
            "https://test.com", "", status_code=200, headers=headers
        )

        # call tested function - ok status is OK
        self.assertTrue(response.is_valid())

        response = PageResponseObject(
            "https://test.com", "", status_code=300, headers=headers
        )
        # call tested function - redirect status is OK
        self.assertTrue(response.is_valid())

        response = PageResponseObject(
            "https://test.com", "", status_code=301, headers=headers
        )
        # call tested function - redirect status is OK
        self.assertTrue(response.is_valid())

        response = PageResponseObject(
            "https://test.com", "", status_code=304, headers=headers
        )
        # call tested function - redirect status is OK
        self.assertTrue(response.is_valid())

        response = PageResponseObject(
            "https://test.com", "", status_code=403, headers=headers
        )
        # call tested function
        self.assertTrue(response.is_valid())

    def test_is_valid__status(self):
        headers = {"Content-Type": "text/html"}
        response = PageResponseObject(
            "https://test.com", "", status_code=100, headers=headers
        )
        # call tested function
        self.assertFalse(response.is_valid())

        response = PageResponseObject(
            "https://test.com", "", status_code=400, headers=headers
        )
        # call tested function
        self.assertFalse(response.is_valid())

        response = PageResponseObject(
            "https://test.com", "", status_code=401, headers=headers
        )
        # call tested function
        self.assertFalse(response.is_valid())

        response = PageResponseObject(
            "https://test.com", "", status_code=402, headers=headers
        )
        # call tested function
        self.assertFalse(response.is_valid())

        response = PageResponseObject(
            "https://test.com", "", status_code=404, headers=headers
        )
        # call tested function
        self.assertFalse(response.is_valid())

        response = PageResponseObject(
            "https://test.com", "", status_code=405, headers=headers
        )
        # call tested function
        self.assertFalse(response.is_valid())

        response = PageResponseObject(
            "https://test.com", "", status_code=500, headers=headers
        )
        # call tested function
        self.assertFalse(response.is_valid())

    def test_is_headers_empty__true(self):
        headers = {}
        response = PageResponseObject(
            "https://test.com", "", status_code=200, headers=headers
        )

        self.assertTrue(response.is_headers_empty())

    def test_is_headers_empty__false(self):
        headers = {"Content-Type": "text/html"}
        response = PageResponseObject(
            "https://test.com", "", status_code=200, headers=headers
        )

        self.assertFalse(response.is_headers_empty())

    def test_get_charset__quotes(self):
        headers = {"Content-Type": 'text/html; charset="UTF-8"'}
        response = PageResponseObject(
            "https://test.com", "", status_code=200, headers=headers
        )

        self.assertEqual(response.get_content_type_charset(), "UTF-8")

    def test_get_charset__no_quotes(self):
        headers = {"Content-Type": "text/html; charset=UTF-8"}
        response = PageResponseObject(
            "https://test.com", "", status_code=200, headers=headers
        )

        self.assertEqual(response.get_content_type_charset(), "UTF-8")

    def test_is_content_html(self):
        headers = {"Content-Type": "text/html; charset=UTF-8"}
        response = PageResponseObject(
            "https://test.com", "", status_code=200, headers=headers
        )

        self.assertTrue(response.is_content_html())
        self.assertFalse(response.is_content_rss())

    def test_is_content_rss(self):
        headers = {"Content-Type": "text/rss; charset=UTF-8"}
        response = PageResponseObject(
            "https://test.com", "", status_code=200, headers=headers
        )

        self.assertTrue(response.is_content_rss())
        self.assertFalse(response.is_content_html())


class UrlTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_p_is_html(self):
        MockRequestCounter.mock_page_requests = 0

        # call tested function
        url = Url("https://multiple-favicons/page.html")

        self.assertEqual(type(url.p), HtmlPage)
        self.assertEqual(MockRequestCounter.mock_page_requests, 1)

    def test_is_valid__true(self):
        MockRequestCounter.mock_page_requests = 0
        url = Url("https://multiple-favicons/page.html")

        self.assertEqual(type(url.p), HtmlPage)

        # call tested function
        self.assertTrue(url.is_valid())

        self.assertEqual(MockRequestCounter.mock_page_requests, 1)

    def test_is_valid__false_response_invalid(self):
        MockRequestCounter.mock_page_requests = 0

        link = "https://multiple-favicons/page.html"
        url = Url(link)

        self.assertEqual(type(url.p), HtmlPage)
        url.response = PageResponseObject(link, None, status_code=500)

        # call tested function
        self.assertFalse(url.is_valid())

        self.assertEqual(MockRequestCounter.mock_page_requests, 1)

    def test_is_valid__false_p_is_None(self):
        MockRequestCounter.mock_page_requests = 0
        url = Url("https://multiple-favicons/page.html")

        self.assertEqual(type(url.p), HtmlPage)
        url.p = None

        self.assertFalse(url.is_valid())

        self.assertEqual(MockRequestCounter.mock_page_requests, 1)

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

    def test_get_last_modified(self):
        MockRequestCounter.mock_page_requests = 0

        handler = Url("https://page-with-last-modified-header.com")

        response = handler.get_response()

        self.assertTrue(response)

        last_modified = response.get_last_modified()
        self.assertTrue(last_modified)
