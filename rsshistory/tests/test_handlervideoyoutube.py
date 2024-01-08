from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .utilities import WebPageDisabled
from ..pluginentries.handlervideoyoutube import YouTubeVideoHandler


class YouTubeLinksTest(WebPageDisabled, TestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_link_input2code(self):
        handler = YouTubeVideoHandler("https://www.youtube.com/watch?v=1234")
        self.assertEqual(handler.get_video_code(), "1234")

    def test_link_input2code_with_time(self):
        handler = YouTubeVideoHandler(
            "https://www.youtube.com/watch?v=uN_ab1GTXvY&t=50s"
        )
        self.assertEqual(handler.get_video_code(), "uN_ab1GTXvY")

    def test_link_input2code_with_time_order(self):
        handler = YouTubeVideoHandler(
            "https://www.youtube.com/watch?t=50s&v=uN_ab1GTXvY"
        )
        self.assertEqual(handler.get_video_code(), "uN_ab1GTXvY")

    def test_link_youtu_input2code(self):
        handler = YouTubeVideoHandler("https://youtu.be/1234")
        self.assertEqual(handler.get_video_code(), "1234")

    def test_link_youtu_input2code_with_time(self):
        handler = YouTubeVideoHandler("https://www.youtu.be/1234?t=50")
        self.assertEqual(handler.get_video_code(), "1234")

    def test_link_code2url(self):
        self.assertEqual(
            YouTubeVideoHandler.code2url("1234"), "https://www.youtube.com/watch?v=1234"
        )
