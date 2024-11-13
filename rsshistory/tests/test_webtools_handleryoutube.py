from ..webtools import YouTubeVideoHandler, YouTubeChannelHandler

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class YouTubeVideoHandlerTest(FakeInternetTestCase):

    def test_constructor(self):
        MockRequestCounter.mock_page_requests = 0

        test_link = "https://www.youtube.com/watch?v=123"
        handler = YouTubeVideoHandler(test_link)
        self.assertEqual(handler.url, test_link)

    def test_get_channel_code(self):
        test_link = "https://www.youtube.com/watch?v=123"
        handler = YouTubeVideoHandler(test_link)
        self.assertEqual(handler.get_video_code(), "123")

    def test_get_link_embed(self):
        test_link = "https://www.youtube.com/watch?v=123"

        handler = YouTubeVideoHandler(test_link)
        link_embed = handler.get_link_embed()
        self.assertEqual(link_embed, "https://www.youtube.com/embed/123")


class YouTubeChannelHandlerTest(FakeInternetTestCase):
    def test_constructor__rss(self):
        MockRequestCounter.mock_page_requests = 0

        handler = YouTubeChannelHandler(
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"
        )
        self.assertEqual(
            handler.url,
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM",
        )

    def test_constructor__html(self):
        MockRequestCounter.mock_page_requests = 0

        test_link = "https://www.youtube.com/channel/1234"
        handler = YouTubeChannelHandler(test_link)
        self.assertEqual(handler.url, test_link)
