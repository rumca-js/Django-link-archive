from ..webtools import (
    WebConfig,
)

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class WebConfigTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_get_browsers(self):
        browsers = WebConfig.get_browsers()
        self.assertTrue(len(browsers) > 0)

        self.assertIn("RequestsCrawler", browsers)

    def test_get_init_crawler_config(self):
        config = WebConfig.get_init_crawler_config()
        self.assertTrue(len(config) > 0)

    def test_get_init_crawler_config(self):
        crawler = WebConfig.get_crawler_from_string("RequestsCrawler")
        self.assertTrue(crawler)

        crawler = WebConfig.get_crawler_from_string("SeleniumChromeHeadless")
        self.assertTrue(crawler)

        crawler = WebConfig.get_crawler_from_string("StealthRequestsCrawler")
        self.assertTrue(crawler)
