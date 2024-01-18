from ..pluginentries.handlerchannelyoutube import YouTubeChannelHandler
from .fakeinternet import FakeInternetTestCase


class YouTubeChannelHandlerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_source_input2code_channel(self):
        self.assertEqual(
            YouTubeChannelHandler(
                "https://www.youtube.com/channel/1234"
            ).get_channel_code(),
            "1234",
        )

    def test_source_input2code_feed(self):
        self.assertEqual(
            YouTubeChannelHandler(
                "https://www.youtube.com/feeds/videos.xml?channel_id=1234"
            ).get_channel_code(),
            "1234",
        )

    def test_source_code2url(self):
        self.assertEqual(
            YouTubeChannelHandler("1234").get_channel_url(),
            "https://www.youtube.com/channel/1234",
        )

    def test_source_code2feed(self):
        self.assertEqual(
            YouTubeChannelHandler("1234").get_channel_feed(),
            "https://www.youtube.com/feeds/videos.xml?channel_id=1234",
        )
