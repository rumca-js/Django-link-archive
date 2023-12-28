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

        props = url.get_props()
        self.assertTrue(props)
        self.assertEqual(props["link"], "https://www.youtube.com/watch?v=e_QQamQt5x4")

    def test_video_mobile_youtube_handler(self):
        url = EntryUrlInterface("https://m.youtube.com/watch?v=e_QQamQt5x4")

        props = url.get_props()
        self.assertTrue(props)
        self.assertEqual(props["link"], "https://www.youtube.com/watch?v=e_QQamQt5x4")

    def test_video_youtu_be_handler(self):
        url = EntryUrlInterface("https://youtu.be/e_QQamQt5x4")

        props = url.get_props()
        self.assertTrue(props)
        self.assertEqual(props["link"], "https://www.youtube.com/watch?v=e_QQamQt5x4")

    def test_html_handler(self):
        url = EntryUrlInterface("https://www.linkedin.com")
        props = url.get_props()

        self.assertTrue(props)

    def test_rss_handler(self):
        url = EntryUrlInterface("https://rsspage.com/rss.xml")
        props = url.get_props()

        self.assertTrue(props)
        self.assertTrue(len(props) > 0)

        self.assertTrue(props["title"])
        self.assertTrue(props["description"])

    """
    def test_rss_old_pubdate(self):
        url = EntryUrlInterface("https://youtube.com/channel/2020-year-channel/rss.xml")
        props = url.get_props()

        self.assertTrue(props)
        self.assertTrue(len(props) > 0)

        self.assertTrue(props["date_published"])
        self.assertEqual(props["date_published"].year, 2020)

    def test_rss_no_pubdate(self):
        url = EntryUrlInterface("https://youtube.com/channel/no-pubdate-channel/rss.xml")
        props = url.get_props()

        self.assertTrue(props)
        self.assertTrue(len(props) > 0)

        self.assertTrue(props["date_published"])
        self.assertEqual(props["date_published"].year, 2023)
    """
