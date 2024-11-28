from ..webtools import (
   YouTubeVideoHandler,
   YouTubeChannelHandler,
   YouTubeJsonHandler,
)
from ..pluginurl import UrlHandler

from .fakeinternet import FakeInternetTestCase, MockRequestCounter, YouTubeJsonHandlerMock


class YouTubeJsonHandlerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_constructor(self):
        MockRequestCounter.mock_page_requests = 0

        test_link = "https://www.youtube.com/watch?v=123"

        # call tested function
        handler = YouTubeJsonHandlerMock(test_link, url_builder=UrlHandler)

        self.assertEqual(handler.url, test_link)
        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_get_video_code(self):
        MockRequestCounter.mock_page_requests = 0
        test_link = "https://www.youtube.com/watch?v=123"
        handler = YouTubeJsonHandlerMock(test_link, url_builder=UrlHandler)

        # call tested function
        self.assertEqual(handler.get_video_code(), "123")
        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_get_link_embed(self):
        MockRequestCounter.mock_page_requests = 0
        test_link = "https://www.youtube.com/watch?v=123"

        handler = YouTubeJsonHandlerMock(test_link, url_builder=UrlHandler)

        # call tested function
        link_embed = handler.get_link_embed()
        self.assertEqual(link_embed, "https://www.youtube.com/embed/123")
        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_get_response(self):
        MockRequestCounter.mock_page_requests = 0
        test_link = "https://www.youtube.com/watch?v=123"

        handler = YouTubeJsonHandlerMock(test_link, url_builder=UrlHandler)

        # call tested function
        response = handler.get_response()

        self.assertTrue(response)
        self.assertEqual(MockRequestCounter.mock_page_requests, 1)

    def test_get_contents_hash(self):
        MockRequestCounter.mock_page_requests = 0
        test_link = "https://www.youtube.com/watch?v=123"

        handler = YouTubeJsonHandlerMock(test_link, url_builder=UrlHandler)

        # call tested function
        hash = handler.get_contents_hash()

        self.assertTrue(hash)

    def test_get_contents_body_hash(self):
        MockRequestCounter.mock_page_requests = 0
        test_link = "https://www.youtube.com/watch?v=123"

        handler = YouTubeJsonHandlerMock(test_link, url_builder=UrlHandler)

        # call tested function
        hash = handler.get_contents_body_hash()

        self.assertTrue(hash)

    def test_get_contents(self):
        MockRequestCounter.mock_page_requests = 0
        test_link = "https://www.youtube.com/watch?v=123"

        handler = YouTubeJsonHandlerMock(test_link, url_builder=UrlHandler)

        # call tested function
        contents = handler.get_contents()

        self.assertTrue(contents)

    def test_get_response(self):
        MockRequestCounter.mock_page_requests = 0
        test_link = "https://www.youtube.com/watch?v=123"

        handler = YouTubeJsonHandlerMock(test_link, url_builder=UrlHandler)

        # call tested function
        response = handler.get_response()

        self.assertTrue(response)


class YouTubeChannelHandlerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_constructor__rss(self):
        MockRequestCounter.mock_page_requests = 0

        # call tested function
        handler = YouTubeChannelHandler(
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM",
            url_builder=UrlHandler
        )
        self.assertEqual(
            handler.url,
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM",
        )

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_constructor__html(self):
        MockRequestCounter.mock_page_requests = 0

        test_link = "https://www.youtube.com/channel/1234"
        # call tested function
        handler = YouTubeChannelHandler(test_link, url_builder=UrlHandler)
        self.assertEqual(handler.url, test_link)

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_constructor__user(self):
        MockRequestCounter.mock_page_requests = 0

        test_link = "https://www.youtube.com/user/1234"
        # call tested function
        handler = YouTubeChannelHandler(test_link, url_builder=UrlHandler)
        self.assertEqual(handler.url, test_link)

        # +1 - obtains channel code from HTML
        self.assertEqual(MockRequestCounter.mock_page_requests, 1)

    def test_get_channel_url(self):
        MockRequestCounter.mock_page_requests = 0

        handler = YouTubeChannelHandler(
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"
        )

        # call tested function
        channel_name = handler.get_channel_url()

        self.assertEqual(
            channel_name,
            "https://www.youtube.com/channel/SAMTIMESAMTIMESAMTIMESAM",
        )

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_get_response(self):
        MockRequestCounter.mock_page_requests = 0

        handler = YouTubeChannelHandler(
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM",
            url_builder=UrlHandler
        )

        # call tested function
        response = handler.get_response()

        self.assertTrue(response)

        self.assertEqual(MockRequestCounter.mock_page_requests, 1)

    def test_get_contents_hash(self):
        MockRequestCounter.mock_page_requests = 0
        handler = YouTubeChannelHandler(
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM",
            url_builder=UrlHandler
        )

        # call tested function
        hash = handler.get_contents_hash()

        self.assertTrue(hash)

    def test_get_contents_body_hash(self):
        MockRequestCounter.mock_page_requests = 0
        handler = YouTubeChannelHandler(
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM",
            url_builder=UrlHandler
        )

        # call tested function
        hash = handler.get_contents_body_hash()

        self.assertTrue(hash)

    def test_get_contents(self):
        MockRequestCounter.mock_page_requests = 0
        test_link = "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"

        handler = YouTubeChannelHandler(
            test_link,
            url_builder=UrlHandler
        )

        # call tested function
        contents = handler.get_contents()

        self.assertTrue(contents)

    def test_get_response(self):
        MockRequestCounter.mock_page_requests = 0
        test_link = "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"

        handler = YouTubeChannelHandler(
            test_link,
            url_builder=UrlHandler
        )

        # call tested function
        response = handler.get_response()

        self.assertTrue(response)
