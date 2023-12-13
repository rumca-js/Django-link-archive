from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .utilities import WebPageDisabled
from ..pluginentries.handlerurl import HandlerUrl
from ..pluginentries.handlervideoyoutube import YouTubeVideoHandler


class YouTubeVideoHandlerMock(YouTubeVideoHandler):
    def __init__(self, url=None):
        super().__init__(url)

    def download_details_yt(self):
        self.yt_text = """{"_filename" : "test.txt",
        "title" : "test.txt",
        "description" : "test.txt",
        "channel_url" : "https://youtube.com/channel/test.txt",
        "channel" : "JoYoe",
        "id" : "3433",
        "channel_id" : "JoYoe",
        "thumbnail" : "https://youtube.com/files/whatever.png",
        "upload_date" : "20231113"
        }"""
        return True

    def download_details_rd(self):
        self.rd_text = """{}"""
        return True


class HandlerUrlTest(WebPageDisabled, TestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_video_youtube_handler(self):
        url = HandlerUrl("https://www.youtube.com/watch?v=e_QQamQt5x4")
        url.youtube_video_handler = YouTubeVideoHandlerMock

        props = url.get_props()
        self.assertTrue(props)

    def test_html_handler(self):
        url = HandlerUrl("https://www.linkedin.com")
        props = url.get_props()

        self.assertTrue(props)

    def test_rss_handler(self):
        url = HandlerUrl("https://rsspage.com/rss.xml")
        props = url.get_props()

        self.assertTrue(props)
