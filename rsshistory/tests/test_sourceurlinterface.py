from ..models import SourceDataModel
from ..pluginsources.sourceurlinterface import SourceUrlInterface

from .fakeinternet import FakeInternetTestCase


class SourceUrlInterfaceTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_rss(self):
        self.mock_page_requests = 0

        url = SourceUrlInterface("https://www.codeproject.com/WebServices/NewsRSS.aspx")
        props = url.get_props()

        self.assertTrue(props)
        self.assertTrue("url" in props)
        self.assertTrue("title" in props)
        self.assertEqual(props["source_type"], SourceDataModel.SOURCE_TYPE_RSS)

        self.assertEqual(self.mock_page_requests, 1)

    def test_youtube_channel(self):
        self.mock_page_requests = 0

        url = SourceUrlInterface(
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"
        )
        props = url.get_props()

        self.assertTrue(props)
        self.assertTrue("url" in props)
        self.assertTrue("title" in props)
        self.assertEqual(props["source_type"], SourceDataModel.SOURCE_TYPE_YOUTUBE)

        self.assertEqual(self.mock_page_requests, 1)

    def test_youtube_video(self):
        url = SourceUrlInterface("https://www.youtube.com/watch?v=123")
        props = url.get_props()

        self.assertTrue(props)
        self.assertTrue("url" in props)
        self.assertTrue("title" in props)
        self.assertEqual(props["source_type"], SourceDataModel.SOURCE_TYPE_YOUTUBE)

    def test_html(self):
        self.mock_page_requests = 0

        url = SourceUrlInterface("https://linkedin.com")
        props = url.get_props()

        self.assertTrue(props)
        self.assertTrue("url" in props)
        self.assertTrue("title" in props)

        self.assertEqual(props["title"], "LinkedIn Page title")
        self.assertEqual(props["source_type"], SourceDataModel.SOURCE_TYPE_PARSE)

        self.assertEqual(self.mock_page_requests, 1)

    def test_json_source(self):
        url = SourceUrlInterface("https://instance.com/apps/rsshistory/source-json/100")
        props = url.get_props()

        self.assertTrue(props)
        self.assertTrue("url" in props)
        self.assertTrue("title" in props)
        self.assertTrue("proxy_location" in props)

        self.assertEqual(props["title"], "Source100 - Proxy")
        self.assertEqual(
            props["url"], "https://instance.com/apps/rsshistory/source-json/100"
        )
        self.assertEqual(
            props["proxy_location"],
            "https://instance.com/apps/rsshistory/source-json/100",
        )
        self.assertEqual(props["source_type"], SourceDataModel.SOURCE_TYPE_JSON)

    def test_json_sources(self):
        url = SourceUrlInterface("https://instance.com/apps/rsshistory/sources-json")
        props = url.get_props()

        self.assertTrue(props)
        self.assertTrue("url" in props)
        self.assertTrue("title" in props)

        self.assertEqual(props["title"], "Instance Proxy")
        self.assertEqual(props["source_type"], SourceDataModel.SOURCE_TYPE_JSON)
        self.assertEqual(
            props["proxy_location"], "https://instance.com/apps/rsshistory/sources-json"
        )
