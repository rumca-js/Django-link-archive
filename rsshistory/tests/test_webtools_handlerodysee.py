from ..webtools import OdyseeVideoHandler, OdyseeChannelHandler

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class OdyseeVideoHandlerTest(FakeInternetTestCase):
    def test_constructor(self):
        MockRequestCounter.mock_page_requests = 0

        handler = OdyseeVideoHandler("https://odysee.com/@samtime:1/apple-reacts-to-leaked-windows-12:1?test")
        self.assertEqual(handler.url, "https://odysee.com/@samtime:1/apple-reacts-to-leaked-windows-12:1")
        self.assertEqual(handler.get_channel_code(), "@samtime:1")
        self.assertEqual(handler.get_video_code(), "apple-reacts-to-leaked-windows-12:1")


class OdyseeChannelHandlerTest(FakeInternetTestCase):
    def test_constructor__channel_url(self):
        MockRequestCounter.mock_page_requests = 0

        handler = OdyseeChannelHandler("https://odysee.com/@samtime:1?test")
        self.assertEqual(handler.url, "https://odysee.com/@samtime:1?test")
        self.assertEqual(handler.code2url(handler.code), "https://odysee.com/@samtime:1")
        self.assertEqual(handler.code2feed(handler.code), "https://odysee.com/$/rss/@samtime:1")

    def test_constructor__feed_url(self):
        MockRequestCounter.mock_page_requests = 0

        handler = OdyseeChannelHandler("https://odysee.com/$/rss/@samtime:1?test")
        self.assertEqual(handler.url, "https://odysee.com/$/rss/@samtime:1?test")
        self.assertEqual(handler.code2url(handler.code), "https://odysee.com/@samtime:1")
        self.assertEqual(handler.code2feed(handler.code), "https://odysee.com/$/rss/@samtime:1")
