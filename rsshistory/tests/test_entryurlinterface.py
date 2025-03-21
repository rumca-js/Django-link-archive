from utils.dateutils import DateUtils
from ..webtools import YouTubeVideoHandler

from ..pluginurl.entryurlinterface import EntryUrlInterface
from ..controllers import SourceDataController
from ..configuration import Configuration
from ..configuration import Configuration

from .fakeinternet import FakeInternetTestCase


class EntryUrlInterfaceTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_video_youtube_handler(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_remove_links = 0
        conf.days_to_move_to_archive = 0
        conf.save()

        test_link = "https://www.youtube.com/watch?v=archived"
        url = EntryUrlInterface(test_link)

        expected_date_published = DateUtils.from_string(
            "2023-11-13;00:00", "%Y-%m-%d;%H:%M"
        )
        expected_date_published = DateUtils.to_utc_date(expected_date_published)

        props = url.get_props()
        self.assertTrue(props)
        self.assertEqual(props["link"], test_link)
        self.assertEqual(props["title"], "Title")
        self.assertEqual(props["status_code"], 200)
        self.assertEqual(props["page_rating"], 80)
        self.assertTrue(props["date_dead_since"] is None)
        # self.assertEqual(props["date_published"], expected_date_published)

    def test_video_mobile_youtube_handler(self):
        url = EntryUrlInterface("https://m.youtube.com/watch?v=1234")

        props = url.get_props()
        self.assertTrue(props)
        self.assertEqual(props["link"], "https://www.youtube.com/watch?v=1234")
        self.assertEqual(props["title"], "YouTube 1234 video")
        self.assertEqual(props["status_code"], 200)
        self.assertEqual(props["page_rating"], 80)

    def test_video_youtu_be_handler(self):
        url = EntryUrlInterface("https://youtu.be/1234")

        props = url.get_props()
        self.assertTrue(props)
        self.assertEqual(props["link"], "https://www.youtube.com/watch?v=1234")
        self.assertEqual(props["title"], "YouTube 1234 video")
        self.assertEqual(props["status_code"], 200)
        self.assertEqual(props["page_rating"], 80)

    def test_html_handler(self):
        url = EntryUrlInterface("https://www.linkedin.com")
        props = url.get_props()

        self.assertTrue(props)
        self.assertEqual(props["status_code"], 200)
        self.assertEqual(props["page_rating"], 80)
        self.assertTrue(props["date_dead_since"] is None)

    def test_rss_handler(self):
        url = EntryUrlInterface("https://rsspage.com/rss.xml")
        props = url.get_props()

        self.assertTrue(props)
        self.assertTrue(len(props) > 0)

        self.assertTrue(props["title"])
        self.assertTrue(props["description"])
        self.assertEqual(props["status_code"], 200)
        self.assertEqual(props["page_rating"], 80)
        self.assertTrue(props["date_dead_since"] is None)

    def test_error_html(self):
        url = EntryUrlInterface("https://page-with-http-status-500.com")

        props = url.get_props()
        self.assertTrue(props)
        self.assertEqual(props["link"], "https://page-with-http-status-500.com")
        self.assertEqual(props["status_code"], 500)

    def test_youtube_feed(self):
        url = EntryUrlInterface(
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"
        )

        props = url.get_props()
        self.assertTrue(props)

    def test_video_inherits_language(self):
        source_link = "https://youtube.com"
        source_obj = SourceDataController.objects.create(
            url=source_link,
            title="The first link",
            language="ch",
        )

        url = EntryUrlInterface("https://www.youtube.com/watch?v=1234")

        props = url.get_props(source_obj=source_obj)
        self.assertTrue(props)
        self.assertEqual(props["link"], "https://www.youtube.com/watch?v=1234")
        self.assertEqual(props["language"], "ch")
