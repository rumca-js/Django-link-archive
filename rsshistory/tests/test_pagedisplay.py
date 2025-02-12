from sqlalchemy import (
    create_engine,
)
from pathlib import Path

from ..webtools import (
    RssPage,
    HtmlPage,
    YouTubeVideoHandler,
    FeedClient,
    UrlAgeModerator,
)
from utils.sqlmodel import SqlModel, EntriesTable, SourcesTable
from utils.serializers import PageDisplay

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class PageDisplayTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_html_url(self):
        MockRequestCounter.mock_page_requests = 0

        page_display = PageDisplay("https://linkedin.com")

        # one for page, one for rss
        self.assertEqual(MockRequestCounter.mock_page_requests, 1)

    def test_youtube(self):
        MockRequestCounter.mock_page_requests = 0

        page_display = PageDisplay(
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"
        )

        # one for page, one for rss
        self.assertEqual(MockRequestCounter.mock_page_requests, 1)

    def test_rss(self):
        MockRequestCounter.mock_page_requests = 0

        page_display = PageDisplay("https://rsspage.com/rss.xml")

        # one for page, one for rss
        self.assertEqual(MockRequestCounter.mock_page_requests, 1)
