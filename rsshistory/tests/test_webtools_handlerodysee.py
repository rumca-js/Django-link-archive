from ..webtools import OdyseeVideoHandler, OdyseeChannelHandler
from ..pluginurl import UrlHandler

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class OdyseeVideoHandlerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_constructor(self):
        MockRequestCounter.mock_page_requests = 0

        handler = OdyseeVideoHandler(
            "https://odysee.com/@samtime:1/apple-reacts-to-leaked-windows-12:1?test",
            url_builder=UrlHandler
        )
        self.assertEqual(
            handler.url,
            "https://odysee.com/@samtime:1/apple-reacts-to-leaked-windows-12:1",
        )

    def test_get_channel_code(self):
        handler = OdyseeVideoHandler(
            "https://odysee.com/@samtime:1/apple-reacts-to-leaked-windows-12:1?test",
            url_builder=UrlHandler
        )
        self.assertEqual(handler.get_channel_code(), "@samtime:1")

    def test_is_handled_by__channel_video(self):
        handler = OdyseeVideoHandler(
            "https://odysee.com/@samtime:1/apple-reacts-to-leaked-windows-12:1?test",
            url_builder=UrlHandler
        )
        self.assertTrue(handler.is_handled_by())

    def test_is_handled_by__video(self):
        handler = OdyseeVideoHandler(
            "https://odysee.com/ridiculous-zendesk-vulnerability-causes:01c863c36e86789070adf02eaa5c0778975507d5",
            url_builder=UrlHandler
        )
        self.assertTrue(handler.is_handled_by())

    def test_get_video_code__channel_video(self):
        handler = OdyseeVideoHandler(
            "https://odysee.com/@samtime:1/apple-reacts-to-leaked-windows-12:1?test",
            url_builder=UrlHandler
        )
        code = handler.get_video_code()
        self.assertEqual(code, "apple-reacts-to-leaked-windows-12:1")

    def test_get_video_code__channel_video(self):
        handler = OdyseeVideoHandler(
            "https://odysee.com/ridiculous-zendesk-vulnerability-causes:01c863c36e86789070adf02eaa5c0778975507d5",
            url_builder=UrlHandler
        )
        code = handler.get_video_code()
        self.assertEqual(
            code,
            "ridiculous-zendesk-vulnerability-causes:01c863c36e86789070adf02eaa5c0778975507d5",
        )

    def test_get_link_embed(self):
        handler = OdyseeVideoHandler(
            "https://odysee.com/ridiculous-zendesk-vulnerability-causes:01c863c36e86789070adf02eaa5c0778975507d5",
            url_builder=UrlHandler
        )
        link_embed = handler.get_link_embed()
        self.assertEqual(
            link_embed,
            "https://odysee.com/$/embed/ridiculous-zendesk-vulnerability-causes:01c863c36e86789070adf02eaa5c0778975507d5",
        )

    def test_get_contents_hash(self):
        test_link = "https://odysee.com/ridiculous-zendesk-vulnerability-causes:01c863c36e86789070adf02eaa5c0778975507d5"

        handler = OdyseeVideoHandler(test_link, url_builder=UrlHandler)

        # call tested function
        hash = handler.get_contents_hash()

        self.assertTrue(hash)

    def test_get_contents_body_hash(self):
        test_link = "https://odysee.com/ridiculous-zendesk-vulnerability-causes:01c863c36e86789070adf02eaa5c0778975507d5"

        handler = OdyseeVideoHandler(test_link, url_builder=UrlHandler)

        # call tested function
        hash = handler.get_contents_body_hash()

        self.assertTrue(hash)

    def test_get_contents(self):
        test_link = "https://odysee.com/ridiculous-zendesk-vulnerability-causes:01c863c36e86789070adf02eaa5c0778975507d5"

        handler = OdyseeVideoHandler(test_link, url_builder=UrlHandler)

        # call tested function
        contents = handler.get_contents()

        self.assertTrue(contents)

    def test_get_response(self):
        test_link = "https://odysee.com/ridiculous-zendesk-vulnerability-causes:01c863c36e86789070adf02eaa5c0778975507d5"

        handler = OdyseeVideoHandler(test_link, url_builder=UrlHandler)

        # call tested function
        response = handler.get_response()

        self.assertTrue(response)


class OdyseeChannelHandlerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_constructor__channel_url(self):
        MockRequestCounter.mock_page_requests = 0

        # call tested function
        handler = OdyseeChannelHandler("https://odysee.com/@samtime:1?test", url_builder=UrlHandler)

        self.assertEqual(handler.url, "https://odysee.com/@samtime:1?test")
        self.assertEqual(
            handler.code2url(handler.code), "https://odysee.com/@samtime:1"
        )
        self.assertEqual(
            handler.code2feed(handler.code), "https://odysee.com/$/rss/@samtime:1"
        )

    def test_constructor__feed_url(self):
        MockRequestCounter.mock_page_requests = 0

        # call tested function
        handler = OdyseeChannelHandler("https://odysee.com/$/rss/@samtime:1?test", url_builder=UrlHandler)

        self.assertEqual(handler.url, "https://odysee.com/$/rss/@samtime:1?test")
        self.assertEqual(
            handler.code2url(handler.code), "https://odysee.com/@samtime:1"
        )
        self.assertEqual(
            handler.code2feed(handler.code), "https://odysee.com/$/rss/@samtime:1"
        )

    def test_get_contents_hash(self):
        handler = OdyseeChannelHandler("https://odysee.com/@samtime:1?test", url_builder=UrlHandler)

        # call tested function
        hash = handler.get_contents_hash()

        self.assertTrue(hash)

    def test_get_contents_body_hash(self):
        handler = OdyseeChannelHandler("https://odysee.com/@samtime:1?test", url_builder=UrlHandler)

        # call tested function
        hash = handler.get_contents_body_hash()

        self.assertTrue(hash)

    def test_get_contents(self):
        handler = OdyseeChannelHandler("https://odysee.com/@samtime:1?test", url_builder=UrlHandler)

        # call tested function
        contents = handler.get_contents()

        self.assertTrue(contents)

    def test_get_response(self):
        handler = OdyseeChannelHandler("https://odysee.com/@samtime:1?test", url_builder=UrlHandler)

        # call tested function
        response = handler.get_response()

        self.assertTrue(response)
