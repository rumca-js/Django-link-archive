from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from ..pluginentries.handlerchannelyoutube import YouTubeSourceHandler


class YouTubeSourceHandlerTest(TestCase):
    def test_source_input2code_channel(self):
        self.assertEqual(
            YouTubeSourceHandler(
                "https://www.youtube.com/channel/1234"
            ).get_channel_code(),
            "1234",
        )

    def test_source_input2code_feed(self):
        self.assertEqual(
            YouTubeSourceHandler(
                "https://www.youtube.com/feeds/videos.xml?channel_id=1234"
            ).get_channel_code(),
            "1234",
        )

    def test_source_code2url(self):
        self.assertEqual(
            YouTubeSourceHandler("1234").get_channel_url(),
            "https://www.youtube.com/channel/1234",
        )

    def test_source_code2feed(self):
        self.assertEqual(
            YouTubeSourceHandler("1234").get_channel_feed(),
            "https://www.youtube.com/feeds/videos.xml?channel_id=1234",
        )