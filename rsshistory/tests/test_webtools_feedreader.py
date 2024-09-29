from ..webtools import HtmlPage, calculate_hash, FeedReader

from .fake.reddit import (
    reddit_rss_text
)

from .fake.youtube import (
    webpage_youtube_airpano_feed,
    webpage_samtime_youtube_rss,
)

from .fake.thehill import (
    thehill_rss,
)

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class FeedreaderTest(FakeInternetTestCase):
    def test_reddit(self):
        MockRequestCounter.mock_page_requests = 0

        # default language
        p = FeedReader.parse(reddit_rss_text)
        self.assertEqual(p.feed.title, "RSS - Really Simple Syndication")
        self.assertEqual(p.feed.link, "https://www.reddit.com/r/rss/.rss")
        self.assertEqual(len(p.entries), 26)

    def test_youtube(self):
        MockRequestCounter.mock_page_requests = 0

        # default language
        p = FeedReader.parse(webpage_youtube_airpano_feed)
        self.assertEqual(p.feed.title, "AirPano VR")
        self.assertEqual(p.feed.link, "http://www.youtube.com/channel/UCUSElbgKZpE4Xdh5aFWG-Ig")
        self.assertEqual(len(p.entries), 26)

    def test_the_hill(self):
        MockRequestCounter.mock_page_requests = 0

        # default language
        p = FeedReader.parse(thehill_rss)
        self.assertEqual(p.feed.title, "The Hill News")
        self.assertEqual(p.feed.link, "https://thehill.com")
        self.assertEqual(len(p.entries), 26)
