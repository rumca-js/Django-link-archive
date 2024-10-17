from ..webtools import YouTubeVideoHandler

from ..pluginurl.entryurlinterface import EntryUrlInterface
from ..controllers import SourceDataController
from ..configuration import Configuration
from .fakeinternet import FakeInternetTestCase


class EntryUrlInterfaceTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_video_youtube_handler(self):
        url = EntryUrlInterface("https://www.youtube.com/watch?v=1234")

        props = url.get_props()
        self.assertTrue(props)
        self.assertEqual(props["link"], "https://www.youtube.com/watch?v=1234")
        self.assertEqual(props["title"], "1234 test title")
        self.assertEqual(props["status_code"], 200)
        self.assertEqual(props["page_rating"], 0)
        self.assertTrue(props["date_dead_since"] is None)

    def test_video_mobile_youtube_handler(self):
        url = EntryUrlInterface("https://m.youtube.com/watch?v=1234")

        props = url.get_props()
        self.assertTrue(props)
        self.assertEqual(props["link"], "https://www.youtube.com/watch?v=1234")
        self.assertEqual(props["title"], "1234 test title")
        self.assertEqual(props["status_code"], 200)
        self.assertEqual(props["page_rating"], 0)

    def test_video_youtu_be_handler(self):
        url = EntryUrlInterface("https://youtu.be/1234")

        props = url.get_props()
        self.assertTrue(props)
        self.assertEqual(props["link"], "https://www.youtube.com/watch?v=1234")
        self.assertEqual(props["title"], "1234 test title")
        self.assertEqual(props["status_code"], 200)
        self.assertEqual(props["page_rating"], 0)

    def test_html_handler(self):
        url = EntryUrlInterface("https://www.linkedin.com")
        props = url.get_props()

        self.assertTrue(props)
        self.assertEqual(props["status_code"], 200)
        self.assertEqual(props["page_rating"], 0)
        self.assertTrue(props["date_dead_since"] is None)

    def test_rss_handler(self):
        url = EntryUrlInterface("https://rsspage.com/rss.xml")
        props = url.get_props()

        self.assertTrue(props)
        self.assertTrue(len(props) > 0)

        self.assertTrue(props["title"])
        self.assertTrue(props["description"])
        self.assertEqual(props["status_code"], 200)
        self.assertEqual(props["page_rating"], 0)
        self.assertTrue(props["date_dead_since"] is None)

    def test_error_html(self):
        url = EntryUrlInterface("https://page-with-http-status-500.com")

        props = url.get_props()
        self.assertTrue(props is None)

    def test_error_rrs(self):
        url = EntryUrlInterface("https://invalid.rsspage.com/rss.xml")

        props = url.get_props()
        self.assertTrue(props is None)

    def test_error_youtube_video(self):
        url = EntryUrlInterface("https://m.youtube.com/watch?v=666")

        props = url.get_props()
        self.assertTrue(props is None)

    def test_youtube_feed(self):
        url = EntryUrlInterface(
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"
        )

        props = url.get_props()
        self.assertTrue(props)

    def test_error_html_ignore_errors(self):
        url = EntryUrlInterface(
            "https://page-with-http-status-500.com", ignore_errors=True
        )

        props = url.get_props()
        self.assertTrue(props)
        self.assertEqual(props["link"], "https://page-with-http-status-500.com")
        self.assertEqual(props["title"], 'Page title') # even though status is 500, response was provided
        self.assertTrue(props["date_dead_since"] is not None)
        self.assertEqual(props["status_code"], 500)

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

    def test_ftp(self):
        url = EntryUrlInterface("ftp://www.linkedin.com", ignore_errors=True)
        props = url.get_props()

        self.assertTrue(props)
        self.assertEqual(props["link"], "ftp://www.linkedin.com")
        self.assertEqual(props["status_code"], 0)

    def test_smb(self):
        url = EntryUrlInterface("smb://www.linkedin.com", ignore_errors=True)
        props = url.get_props()

        self.assertTrue(props)
        self.assertEqual(props["link"], "smb://www.linkedin.com")
        self.assertEqual(props["status_code"], 0)

    def test_smb_ips_accepted(self):
        entry = Configuration.get_object().config_entry
        entry.accept_ip_addresses = True
        entry.save()

        url = EntryUrlInterface("//127.0.0.1/resource", ignore_errors=True)
        props = url.get_props()

        self.assertTrue(props)
        self.assertEqual(props["link"], "//127.0.0.1/resource")
        self.assertEqual(props["status_code"], 0)

    def test_smb_ips_not_accepted(self):
        entry = Configuration.get_object().config_entry
        entry.accept_ip_addresses = False
        entry.save()

        url = EntryUrlInterface("//127.0.0.1/resource", ignore_errors=True)
        props = url.get_props()

        self.assertTrue(props)
        self.assertEqual(props["link"], "//127.0.0.1/resource")
        self.assertEqual(props["status_code"], 0)

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
