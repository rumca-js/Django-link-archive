from ..models import SourceDataModel
from ..pluginsources.sourceurlinterface import SourceUrlInterface
from ..webtools import HtmlPage, RssPage, InternetPageHandler
from ..pluginurl import UrlHandler

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class SourceUrlInterfaceTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_rss(self):
        MockRequestCounter.mock_page_requests = 0

        url = SourceUrlInterface("https://www.codeproject.com/WebServices/NewsRSS.aspx")
        self.assertTrue(type(url.h.get_handler()), InternetPageHandler)
        self.assertTrue(type(url.h.get_handler().p), RssPage)

        props = url.get_props()

        self.assertTrue(props)
        self.assertTrue("url" in props)
        self.assertEqual(
            props["url"], "https://www.codeproject.com/WebServices/NewsRSS.aspx"
        )
        self.assertTrue("title" in props)
        self.assertEqual(props["source_type"], SourceDataModel.SOURCE_TYPE_RSS)

        self.assertEqual(MockRequestCounter.mock_page_requests, 1)

    def test_youtube_channel(self):
        MockRequestCounter.mock_page_requests = 0

        url = SourceUrlInterface(
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"
        )
        self.assertTrue(type(url.h.get_handler()), UrlHandler.youtube_channel_handler)

        props = url.get_props()

        self.assertTrue(props)
        self.assertTrue("url" in props)
        self.assertEqual(
            props["url"],
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM",
        )
        self.assertTrue("title" in props)
        self.assertEqual(props["source_type"], SourceDataModel.SOURCE_TYPE_YOUTUBE)

        self.assertEqual(MockRequestCounter.mock_page_requests, 1)

    def test_youtube_video(self):
        url = SourceUrlInterface("https://www.youtube.com/watch?v=1234")
        self.assertTrue(type(url.h.get_handler()), UrlHandler.youtube_video_handler)

        props = url.get_props()

        self.assertTrue(props)
        self.assertTrue("url" in props)
        self.assertEqual(
            props["url"],
            "https://www.youtube.com/feeds/videos.xml?channel_id=1234-channel-id",
        )
        self.assertTrue("title" in props)
        self.assertEqual(props["source_type"], SourceDataModel.SOURCE_TYPE_YOUTUBE)

    def test_html_parse(self):
        MockRequestCounter.mock_page_requests = 0

        url = SourceUrlInterface("https://linkedin.com")
        self.assertTrue(type(url.h.get_handler()), InternetPageHandler)
        self.assertTrue(type(url.h.get_handler().p), HtmlPage)

        props = url.get_props()

        self.assertTrue(props)
        self.assertTrue("url" in props)
        self.assertEqual(props["url"], "https://linkedin.com")
        self.assertTrue("title" in props)

        self.assertEqual(props["title"], "LinkedIn Page title")
        self.assertEqual(props["source_type"], SourceDataModel.SOURCE_TYPE_PARSE)

        self.assertEqual(MockRequestCounter.mock_page_requests, 1)

    def test_html_rss_link(self):
        MockRequestCounter.mock_page_requests = 0

        url = SourceUrlInterface("https://page-with-rss-link.com")
        self.assertTrue(type(url.h.get_handler()), InternetPageHandler)
        self.assertTrue(type(url.h.get_handler().p), HtmlPage)

        props = url.get_props()

        self.assertTrue(props)
        self.assertTrue("url" in props)
        self.assertEqual(props["url"], "https://page-with-rss-link.com/feed")
        self.assertTrue("title" in props)

        self.assertEqual(props["title"], "Page with RSS link - RSS contents")
        self.assertEqual(props["source_type"], SourceDataModel.SOURCE_TYPE_RSS)

        # two requests -> one for page, second one to obtain RSS properties
        self.assertEqual(MockRequestCounter.mock_page_requests, 2)

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
