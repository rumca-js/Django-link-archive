from ..pluginentries.handlerchannelodysee import OdyseeChannelHandler
from .fakeinternet import FakeInternetTestCase


class OdyseeChannelHandlerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_source_input2code_channel(self):
        self.assertEqual(
            OdyseeChannelHandler("https://odysee.com/@samtime:1").get_channel_code(),
            "@samtime:1",
        )

    def test_source_input2code_feed(self):
        self.assertEqual(
            OdyseeChannelHandler(
                "https://odysee.com/$/rss/@samtime:1"
            ).get_channel_code(),
            "@samtime:1",
        )

    def test_source_code2url(self):
        self.assertEqual(
            OdyseeChannelHandler("1234").get_channel_url(),
            "https://odysee.com/1234",
        )

    def test_source_code2feed(self):
        self.assertEqual(
            OdyseeChannelHandler("1234").get_channel_feed(),
            "https://odysee.com/$/rss/1234",
        )
