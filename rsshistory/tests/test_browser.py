from ..models import Browser

from ..webtools import (
    RequestsCrawler,
    SeleniumChromeHeadless,
    SeleniumChromeFull,
    SeleniumUndetected,
    ServerCrawler,
    ScriptCrawler,
    StealthRequestsCrawler,
)

from .fakeinternet import FakeInternetTestCase


class BrowserTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_read_browser_setup__empty(self):
        Browser.objects.all().delete()

        # call tested function
        Browser.read_browser_setup()

        browsers = Browser.objects.all()
        self.assertTrue(browsers.count() > 0)

    def test_read_browser_setup__nonempty(self):
        Browser.objects.all().delete()

        # call tested function
        Browser.read_browser_setup()

        browsers = Browser.objects.all()
        init_value = browsers.count()

        Browser.read_browser_setup()

        browsers = Browser.objects.all()
        self.assertEqual(init_value, browsers.count())

    def test_get_browser_setup(self):
        Browser.read_browser_setup()
        browsers = Browser.objects.all()
        self.assertTrue(browsers.count() > 0)

        # call tested function
        setup = Browser.get_browser_setup()
        self.assertTrue(len(setup) > 0)

    def test_get_setup(self):
        Browser.objects.all().delete()

        browser = Browser.objects.create(
                name = "test",
                crawler = "RequestsCrawler",
                settings = '{"test_setting" : "something"}',
        )

        # call tested function
        setup = browser.get_setup()
        self.assertTrue(setup["name"], "test")
        self.assertTrue(setup["crawler"], RequestsCrawler)
        self.assertTrue(setup["settings"]["test_setting"], "something")
