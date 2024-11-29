from ..webtools import HtmlPage, RssPage, HttpPageHandler

from ..models import SourceDataModel
from ..pluginsources.sourceurlinterface import SourceUrlInterface
from ..pluginurl import UrlHandler

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class SourceUrlInterfaceTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_rss(self):
        MockRequestCounter.mock_page_requests = 0

        url = SourceUrlInterface("https://www.codeproject.com/WebServices/NewsRSS.aspx")
        # call tested function
        props = url.get_props()

        self.assertEqual(type(url.u.get_handler()), HttpPageHandler)
        self.assertEqual(type(url.u.get_handler().p), RssPage)

        self.assertTrue(props)
        self.assertTrue("url" in props)
        self.assertEqual(
            props["url"], "https://www.codeproject.com/WebServices/NewsRSS.aspx"
        )
        self.assertTrue("title" in props)
        self.assertEqual(props["source_type"], SourceDataModel.SOURCE_TYPE_RSS)

        self.assertTrue("category_name" in props)
        self.assertEqual(props["category_name"], "New")
        self.assertTrue("subcategory_name" in props)
        self.assertEqual(props["subcategory_name"], "New")

        self.assertEqual(MockRequestCounter.mock_page_requests, 1)

    def test_youtube_channel(self):
        MockRequestCounter.mock_page_requests = 0

        url = SourceUrlInterface(
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"
        )

        # call tested function
        props = url.get_props()

        self.assertEqual(type(url.u.get_handler()), UrlHandler.youtube_channel_handler)

        self.assertTrue(props)
        self.assertTrue("url" in props)
        self.assertEqual(
            props["url"],
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM",
        )
        self.assertTrue("title" in props)
        self.assertEqual(props["source_type"], SourceDataModel.SOURCE_TYPE_YOUTUBE)

        # one call to obtain rss
        # second one to obtain thumbnail (through HTML)
        self.assertEqual(MockRequestCounter.mock_page_requests, 1)

    def test_youtube_video(self):
        url = SourceUrlInterface("https://www.youtube.com/watch?v=1234")

        # call tested function
        props = url.get_props()

        # the result link is for feed, for channel
        self.assertEqual(type(url.u.get_handler()), UrlHandler.youtube_channel_handler)

        self.assertTrue(props)
        self.assertTrue("url" in props)
        self.assertEqual(
            props["url"],
            "https://www.youtube.com/feeds/videos.xml?channel_id=1234-channel-id",
        )
        self.assertTrue("title" in props)
        self.assertEqual(props["source_type"], SourceDataModel.SOURCE_TYPE_YOUTUBE)

    def test_odysee(self):
        url = SourceUrlInterface("https://odysee.com/$/rss/@samtime:0")

        # call tested function
        props = url.get_props()

        self.assertEqual(type(url.u.get_handler()), UrlHandler.odysee_channel_handler)

        self.assertTrue(props)
        self.assertTrue("url" in props)
        self.assertEqual(
            props["url"],
            "https://odysee.com/$/rss/@samtime:0",
        )
        self.assertTrue("title" in props)
        self.assertEqual(props["source_type"], SourceDataModel.SOURCE_TYPE_RSS)

    def test_html_parse(self):
        MockRequestCounter.mock_page_requests = 0

        url = SourceUrlInterface("https://linkedin.com")

        # call tested function
        props = url.get_props()

        self.assertTrue(type(url.u.get_handler()), HttpPageHandler)
        self.assertTrue(type(url.u.get_handler().p), HtmlPage)

        self.assertTrue(props)
        self.assertTrue("url" in props)
        self.assertEqual(props["url"], "https://linkedin.com")
        self.assertTrue("title" in props)

        self.assertEqual(props["title"], "LinkedIn Page title")
        self.assertEqual(props["source_type"], SourceDataModel.SOURCE_TYPE_PARSE)

        # checks if link is RSS
        # checks openrss if has RSS link
        self.assertEqual(MockRequestCounter.mock_page_requests, 2)

    def test_html_rss_link(self):
        MockRequestCounter.mock_page_requests = 0

        url = SourceUrlInterface("https://page-with-rss-link.com")

        # call tested function
        props = url.get_props()

        self.assertEqual(type(url.u.get_handler()), HttpPageHandler)
        # the result link is for RSS link, therefore last handler is for RSS page
        self.assertEqual(type(url.u.get_handler().p), RssPage)

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

        # call tested function
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

        # call tested function
        props = url.get_props()

        self.assertTrue(props)
        self.assertTrue("url" in props)
        self.assertTrue("title" in props)

        self.assertEqual(props["title"], "Instance Proxy")
        self.assertEqual(props["source_type"], SourceDataModel.SOURCE_TYPE_JSON)
        self.assertEqual(
            props["proxy_location"], "https://instance.com/apps/rsshistory/sources-json"
        )

    def test_reddit_channel(self):
        MockRequestCounter.mock_page_requests = 0

        url = SourceUrlInterface("https://www.reddit.com/r/searchengines/")

        # call tested function
        props = url.get_props()

        self.assertEqual(type(url.u.get_handler()), HttpPageHandler)
        self.assertEqual(type(url.u.get_handler().p), RssPage)

        self.assertTrue(props)
        self.assertTrue("url" in props)
        self.assertEqual(props["url"], "https://www.reddit.com/r/searchengines/.rss")
        self.assertTrue("title" in props)
        self.assertEqual(props["source_type"], SourceDataModel.SOURCE_TYPE_RSS)

        self.assertEqual(MockRequestCounter.mock_page_requests, 1)
