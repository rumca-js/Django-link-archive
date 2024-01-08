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
