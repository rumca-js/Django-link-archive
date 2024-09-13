from sqlalchemy import (
    create_engine,
)
from pathlib import Path

from webtools import RssPage, HtmlPage, YouTubeVideoHandler, FeedClient, UrlAgeModerator
from utils.sqlmodel import SqlModel, EntriesTable, SourcesTable
from utils.alchemysearch import AlchemySearch

from ..pluginurl.urlhandler import UrlHandler
from .fakeinternet import FakeInternetTestCase


class AlchemySearchTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()
        self.found_row = None

    def handle_row(self, row):
        self.found_row = row

    def teardown(self):
        path = Path(self.get_engine_path())
        if path.exists():
            print("Removed engine file")
            path.unlink()

    def get_engine_path(self):
        return "test_feedclient.db"

    def get_engine(self):
        return create_engine("sqlite:///" + self.get_engine_path())

    def test_follow_url__youtube_feed(self):
        self.teardown()

        engine = self.get_engine()
        db = SqlModel(engine=engine)

        test_link = "https://www.youtube.com/feeds/videos.xml?channel_id=UCXuqSBlHAE6Xw-yeJA0Tunw"

        c = FeedClient(engine=engine)
        c.follow_url(db, test_link)
        c.add_entry(db, "https://title-in-head.com")

        search = AlchemySearch(db, "link = https://title-in-head", self)
        search.search()

        self.assertTrue(self.found_row is not None)
