from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from ..pluginentries.youtubelinkhandler import YouTubeLinkHandler
from ..pluginsources.youtubesourcehandler import YouTubeSourceHandler


class YouTubeLinksTest(TestCase):
    def test_link_input2code(self):
        handler = YouTubeLinkHandler("https://www.youtube.com/watch?v=1234")
        self.assertEqual(handler.get_video_code(), "1234")

    def test_link_input2code_with_time(self):
        handler = YouTubeLinkHandler(
            "https://www.youtube.com/watch?v=uN_ab1GTXvY&t=50s"
        )
        self.assertEqual(handler.get_video_code(), "uN_ab1GTXvY")

    def test_link_input2code_with_time_order(self):
        handler = YouTubeLinkHandler(
            "https://www.youtube.com/watch?t=50s&v=uN_ab1GTXvY"
        )
        self.assertEqual(handler.get_video_code(), "uN_ab1GTXvY")

    def test_link_youtu_input2code(self):
        handler = YouTubeLinkHandler("https://youtu.be/1234")
        self.assertEqual(handler.get_video_code(), "1234")

    def test_link_youtu_input2code_with_time(self):
        handler = YouTubeLinkHandler("https://www.youtu.be/1234?t=50")
        self.assertEqual(handler.get_video_code(), "1234")

    def test_link_code2url(self):
        self.assertEqual(
            YouTubeLinkHandler.code2url("1234"), "https://www.youtube.com/watch?v=1234"
        )

    def test_source_input2code_channel(self):
        self.assertEqual(
            YouTubeSourceHandler.input2code("https://www.youtube.com/channel/1234"),
            "1234",
        )

    def test_source_input2code_feed(self):
        self.assertEqual(
            YouTubeSourceHandler.input2code(
                "https://www.youtube.com/feeds/videos.xml?channel_id=1234"
            ),
            "1234",
        )

    def test_source_code2url(self):
        self.assertEqual(
            YouTubeSourceHandler.code2url("1234"),
            "https://www.youtube.com/channel/1234",
        )

    def test_source_code2feed(self):
        self.assertEqual(
            YouTubeSourceHandler.code2feed("1234"),
            "https://www.youtube.com/feeds/videos.xml?channel_id=1234",
        )
