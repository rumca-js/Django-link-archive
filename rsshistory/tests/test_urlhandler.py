from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .utilities import WebPageDisabled
from ..pluginentries.entryurlinterface import UrlHandler
from ..pluginentries.handlervideoyoutube import YouTubeVideoHandler


class UrlHandlerTest(WebPageDisabled, TestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_get_rss(self):
        handler = UrlHandler.get("https://rsspage.com/rss.xml")

        self.assertTrue(handler.is_rss())

    def test_get_html(self):
        handler = UrlHandler.get("https://linkedin.com")

        self.assertTrue(handler.is_html())

    def test_get_youtube_video(self):
        handler = UrlHandler.get("https://www.youtube.com/watch?v=1234")

        self.assertEqual(type(handler), UrlHandler.youtube_video_handler)

    def test_get_youtube_channel(self):
        handler = UrlHandler.get(
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"
        )

        self.assertEqual(type(handler), UrlHandler.youtube_channel_handler)

    def test_rss_get_properties(self):
        handler = UrlHandler.get("https://simple-rss-page.com/rss.xml")

        props = handler.get_properties()

        self.assertEqual(props["title"], "Simple title")
        self.assertEqual(props["description"], "Simple description")

    def test_html_get_properties(self):
        handler = UrlHandler.get("https://linkedin.com")

        props = handler.get_properties()

        self.assertEqual(props["title"], "LinkedIn Page title")
        self.assertEqual(props["description"], "LinkedIn Page description")

    def test_youtube_channel_get_properties(self):
        handler = UrlHandler.get(
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"
        )

        props = handler.get_properties()

        self.assertEqual(props["title"], "SAMTIME on Odysee")

    def test_youtube_channel_get_title(self):
        handler = UrlHandler.get(
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"
        )

        self.assertEqual(handler.get_title(), "SAMTIME on Odysee")