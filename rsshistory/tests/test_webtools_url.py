from ..webtools import (
    Url,
    PageOptions,
    HtmlPage,
    PageResponseObject,
    HttpPageHandler,
)

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

    def test_get_contents__pass(self):
        url = Url("https://multiple-favicons.com/page.html")
        # call tested function
        contents = url.get_contents()
        self.assertTrue(contents != None)

    def test_get_page_options(self):
        page_options = PageOptions()
        page_options.use_full_browser = True

        url = Url("https://multiple-favicons.com/page.html", page_options=page_options)
        # call tested function
        options = url.options
        self.assertTrue(options.use_full_browser)

        page_options = PageOptions()
        page_options.use_headless_browser = True

        url = Url("https://multiple-favicons.com/page.html", page_options=page_options)
        # call tested function
        options = url.options
        self.assertTrue(options.use_headless_browser)

    def test_get_contents__fails(self):
        url = Url("https://page-with-http-status-500.com")

        # call tested function
        contents = url.get_contents()
        self.assertFalse(url.is_valid())

        self.assertEqual(MockRequestCounter.mock_page_requests, 1)

    def test_is_valid__true(self):
        MockRequestCounter.mock_page_requests = 0
        url = Url("https://multiple-favicons.com/page.html")

        self.assertEqual(url.get_handler().p, None)

        url.get_response()

        self.assertEqual(type(url.get_handler().p), HtmlPage)

        # call tested function
        self.assertTrue(url.is_valid())

        self.assertEqual(MockRequestCounter.mock_page_requests, 1)

    def test_is_valid__false_response_invalid(self):
        MockRequestCounter.mock_page_requests = 0

        link = "https://multiple-favicons.com/page.html"
        url = Url(link)

        self.assertEqual(type(url.get_handler()), HttpPageHandler)

        self.assertEqual(url.get_handler().p, None)
        url.get_response()

        self.assertEqual(type(url.get_handler().p), HtmlPage)

        url.response = PageResponseObject(link, None, status_code=500)

        # call tested function
        self.assertFalse(url.is_valid())

        self.assertEqual(MockRequestCounter.mock_page_requests, 1)

    def test_is_valid__false_p_is_None(self):
        MockRequestCounter.mock_page_requests = 0
        url = Url("https://multiple-favicons.com/page.html")

        self.assertEqual(type(url.get_handler()), HttpPageHandler)

        self.assertEqual(url.get_handler().p, None)
        url.get_response()

        self.assertEqual(type(url.get_handler().p), HtmlPage)
        url.handler.p = None

        self.assertFalse(url.is_valid())

        self.assertEqual(MockRequestCounter.mock_page_requests, 1)

    def test_get_favicon(self):
        MockRequestCounter.mock_page_requests = 0
        favicon = Url("https://multiple-favicons.com/page.html").get_favicon()

        self.assertEqual(
            favicon, "https://www.youtube.com/s/desktop/e4d15d2c/img/favicon.ico"
        )

        self.assertEqual(MockRequestCounter.mock_page_requests, 1)

    def test_get_for_page_spotify(self):
        MockRequestCounter.mock_page_requests = 0

        o = PageOptions()
        o.use_full_browser = True
        handler = Url("https://open.spotify.com", page_options=o)

        self.assertEqual(handler.options.use_full_browser, True)

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_get_for_page_youtube(self):
        MockRequestCounter.mock_page_requests = 0

        o = PageOptions()
        o.use_headless_browser = True
        handler = Url("https://open.spotify.com", page_options=o)

        self.assertEqual(handler.options.use_headless_browser, True)

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_get_last_modified(self):
        MockRequestCounter.mock_page_requests = 0

        handler = Url("https://page-with-last-modified-header.com")

        response = handler.get_response()

        self.assertTrue(response)

        last_modified = response.get_last_modified()
        self.assertTrue(last_modified)

        self.assertEqual(MockRequestCounter.mock_page_requests, 1)

    def test_cache_info__is_allowed(self):
        MockRequestCounter.mock_page_requests = 0

        # call tested function
        handler = Url("https://robots-txt.com/page.html")

        domain_info = handler.get_domain_info()
        self.assertTrue(domain_info)
        self.assertEqual(domain_info.url, "https://robots-txt.com")
        self.assertTrue(domain_info.is_allowed("https://robots-txt.com/any"))
        self.assertFalse(domain_info.is_allowed("https://robots-txt.com/admin/"))
        self.assertTrue(domain_info.is_allowed("https://robots-txt.com/admin"))

    def test_get_handler__html_page(self):
        MockRequestCounter.mock_page_requests = 0

        url = Url("https://multiple-favicons.com/page.html")
        url.get_response()

        self.assertEqual(type(url.get_handler()), HttpPageHandler)
        # call tested function
        self.assertEqual(type(url.get_handler().p), HtmlPage)

    def test_get_handler__rss_page(self):
        MockRequestCounter.mock_page_requests = 0

        # call tested function
        url = Url("https://www.codeproject.com/WebServices/NewsRSS.aspx")

        handler = url.get_handler()

        self.assertTrue(type(handler), HttpPageHandler)

    def test_get_handler__youtube_channel(self):
        MockRequestCounter.mock_page_requests = 0

        # call tested function
        url = Url("https://www.youtube.com/feeds/videos.xml?channel_id=UCXuqSBlHAE6Xw-yeJA0Tunw")

        handler = url.get_handler()

        self.assertTrue(type(handler), Url.youtube_channel_handler)

    def test_get_handler__youtube_video(self):
        MockRequestCounter.mock_page_requests = 0

        # call tested function
        url = Url("https://www.youtube.com/watch?v=1234")

        handler = url.get_handler()

        self.assertTrue(type(handler), Url.youtube_video_handler)

    def test_get_type__html_page(self):
        MockRequestCounter.mock_page_requests = 0

        handler = Url.get_type("https://multiple-favicons.com/page.html")

        # call tested function
        self.assertEqual(type(handler), HtmlPage)

    def test_get_handler__rss_page(self):
        MockRequestCounter.mock_page_requests = 0

        # call tested function
        handler = Url.get_type("https://www.codeproject.com/WebServices/NewsRSS.aspx")

        self.assertTrue(type(handler), HtmlPage)

    def test_get_handler__youtube_channel(self):
        MockRequestCounter.mock_page_requests = 0

        # call tested function
        handler = Url.get_type("https://www.youtube.com/feeds/videos.xml?channel_id=UCXuqSBlHAE6Xw-yeJA0Tunw")

        self.assertTrue(type(handler), Url.youtube_channel_handler)

    def test_get_handler__youtube_video(self):
        MockRequestCounter.mock_page_requests = 0

        # call tested function
        handler = Url.get_type("https://www.youtube.com/watch?v=1234")

        self.assertTrue(type(handler), Url.youtube_video_handler)
