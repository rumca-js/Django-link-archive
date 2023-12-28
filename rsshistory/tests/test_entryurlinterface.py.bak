from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .utilities import WebPageDisabled
from ..pluginentries.entryurlinterface import EntryUrlInterface
from ..pluginentries.handlervideoyoutube import YouTubeVideoHandler


class EntryUrlInterfaceTest(WebPageDisabled, TestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_video_youtube_handler(self):
        url = EntryUrlInterface("https://www.youtube.com/watch?v=e_QQamQt5x4")
        # url.youtube_video_handler = YouTubeVideoHandlerMock

        props = url.get_props()
        self.assertTrue(props)

    def test_html_handler(self):
        url = EntryUrlInterface("https://www.linkedin.com")
        props = url.get_props()

        self.assertTrue(props)

    def test_rss_handler(self):
        url = EntryUrlInterface("https://rsspage.com/rss.xml")
        props = url.get_props()

        self.assertTrue(props)
