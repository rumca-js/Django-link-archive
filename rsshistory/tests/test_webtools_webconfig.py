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

    def test_get_init_crawler_config(self):
        config = WebConfig.get_init_crawler_config()
        self.assertTrue(len(config) > 0)
