from sqlalchemy import (
    create_engine,
)
from pathlib import Path

from webtools import RssPage, HtmlPage, YouTubeVideoHandler, FeedClient
from utils.sqlmodel import SqlModel, EntriesTable, SourcesTable

from ..pluginurl.urlhandler import UrlHandler, UrlAgeModerator
from .fakeinternet import FakeInternetTestCase


class FeedClientTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

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
        # call tested function
        c.follow_url(db, test_link)

        Session = db.get_session()
        with Session() as session:
            number_of_source = (
                session.query(SourcesTable)
                .filter(SourcesTable.url == test_link)
                .count()
            )
            self.assertEqual(number_of_source, 1)

        self.teardown()

    def test_follow_url__youtube_feed_twice(self):
        self.teardown()

        engine = self.get_engine()
        db = SqlModel(engine=engine)

        test_link = "https://www.youtube.com/feeds/videos.xml?channel_id=UCXuqSBlHAE6Xw-yeJA0Tunw"

        c = FeedClient(engine=engine)
        # call tested function
        status1 = c.follow_url(db, test_link)
        status2 = c.follow_url(db, test_link)

        self.assertEqual(status1, True)
        self.assertEqual(status2, False)

        Session = db.get_session()
        with Session() as session:
            number_of_source = (
                session.query(SourcesTable)
                .filter(SourcesTable.url == test_link)
                .count()
            )
            self.assertEqual(number_of_source, 1)

        self.teardown()

    def test_follow_url__youtube_channel(self):
        self.teardown()

        engine = self.get_engine()
        db = SqlModel(engine=engine)

        c = FeedClient(engine=engine)
        # call tested function
        c.follow_url(db, "https://www.youtube.com/user/linustechtips")

        Session = db.get_session()
        with Session() as session:
            number_of_source = (
                session.query(SourcesTable)
                .filter(
                    SourcesTable.url
                    == "https://www.youtube.com/feeds/videos.xml?channel_id=UCXuqSBlHAE6Xw-yeJA0Tunw"
                )
                .count()
            )
            self.assertEqual(number_of_source, 1)

        self.teardown()

    def test_unfollow_url__exists(self):
        self.teardown()

        engine = self.get_engine()
        db = SqlModel(engine=engine)

        test_link = "https://www.youtube.com/feeds/videos.xml?channel_id=UCXuqSBlHAE6Xw-yeJA0Tunw"

        c = FeedClient(engine=engine)
        c.follow_url(db, test_link)

        Session = db.get_session()
        with Session() as session:
            number_of_source = (
                session.query(SourcesTable)
                .filter(SourcesTable.url == test_link)
                .count()
            )
            self.assertEqual(number_of_source, 1)

        # call tested function
        status = c.unfollow_url(db, test_link)

        self.assertEqual(status, True)

        Session = db.get_session()
        with Session() as session:
            number_of_source = (
                session.query(SourcesTable)
                .filter(SourcesTable.url == test_link)
                .count()
            )
            self.assertEqual(number_of_source, 0)

        # call tested function
        status = c.unfollow_url(db, test_link)

        self.assertEqual(status, False)

        self.teardown()

    def test_unfollow_all(self):
        self.teardown()

        engine = self.get_engine()
        db = SqlModel(engine=engine)

        test_link = "https://www.youtube.com/feeds/videos.xml?channel_id=UCXuqSBlHAE6Xw-yeJA0Tunw"

        c = FeedClient(engine=engine)
        c.follow_url(db, test_link)

        Session = db.get_session()
        with Session() as session:
            number_of_source = (
                session.query(SourcesTable)
                .filter(SourcesTable.url == test_link)
                .count()
            )
            self.assertEqual(number_of_source, 1)

        # call tested function
        status = c.unfollow_all(db)

        self.assertEqual(status, True)

        Session = db.get_session()
        with Session() as session:
            number_of_source = (
                session.query(SourcesTable).all().count()
            )
            self.assertEqual(number_of_source, 0)

        self.teardown()

    def test_enable_source__disable_source(self):
        self.teardown()

        engine = self.get_engine()
        db = SqlModel(engine=engine)

        test_link = "https://www.youtube.com/feeds/videos.xml?channel_id=UCXuqSBlHAE6Xw-yeJA0Tunw"

        c = FeedClient(engine=engine)
        c.follow_url(db, test_link)

        Session = db.get_session()
        source = None
        with Session() as session:
            source = (
                session.query(SourcesTable).filter(SourcesTable.url == test_link).one()
            )

        self.assertTrue(source is not None)

        # call tested function
        status = c.disable_source(db, source.id)

        self.assertEqual(status, True)

        source = None
        with Session() as session:
            source = (
                session.query(SourcesTable).filter(SourcesTable.url == test_link).one()
            )

        self.assertTrue(source is not None)

        self.assertEqual(source.enabled, False)

        # call tested function
        status = c.enable_source(db, source.id)

        self.assertEqual(status, True)

        with Session() as session:
            source = (
                session.query(SourcesTable).filter(SourcesTable.url == test_link).one()
            )
            self.assertEqual(source.enabled, True)

        self.teardown()

    def test_list_sources(self):
        self.teardown()

        engine = self.get_engine()
        db = SqlModel(engine=engine)

        c = FeedClient(engine=engine)
        # call tested function
        c.list_sources(db)

        self.assertTrue(True)
        self.teardown()

    def test_show_stats(self):
        self.teardown()

        engine = self.get_engine()
        db = SqlModel(engine=engine)

        c = FeedClient(engine=engine)

        # call tested function
        c.show_stats(db)

        self.assertTrue(True)
        self.teardown()

    def test_add_entry(self):
        self.teardown()

        engine = self.get_engine()
        db = SqlModel(engine=engine)

        c = FeedClient(engine=engine)

        # call tested function
        status = c.add_entry(db, "https://page-with-two-links.com")

        self.assertTrue(status)
        self.teardown()

    def test_make_bookmarked(self):
        self.teardown()

        engine = self.get_engine()
        db = SqlModel(engine=engine)
        Session = db.get_session()

        c = FeedClient(engine=engine)

        test_link = "https://page-with-two-links.com"

        # call tested function
        status = c.add_entry(db, test_link)

        id = None
        with Session() as session:
            entries = session.query(EntriesTable).filter(EntriesTable.link == test_link)
            entry = entries.first()
            if entry:
                id = entry.id

        self.assertTrue(id is not None)

        c.make_bookmarked(db, id)

        with Session() as session:
            entries = session.query(EntriesTable).filter(EntriesTable.link == test_link)
            entry = entries.first()
            if entry:
                self.assertEqual(entry.bookmarked, True)

        c.make_not_bookmarked(db, id)

        with Session() as session:
            entries = session.query(EntriesTable).filter(EntriesTable.link == test_link)
            entry = entries.first()
            if entry:
                self.assertEqual(entry.bookmarked, False)