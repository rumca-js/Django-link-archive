from ..models import Browser

from ..webtools import (
    RequestsCrawler,
    SeleniumChromeHeadless,
    SeleniumChromeFull,
    SeleniumUndetected,
    ScriptCrawler,
    StealthRequestsCrawler,
)
from ..configuration import Configuration

from .fakeinternet import FakeInternetTestCase


class BrowserTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_read_browser_setup__empty(self):
        Browser.objects.all().delete()

        # call tested function
        Browser.read_browser_setup()

        browsers = Browser.objects.all()
        self.assertTrue(browsers.count() > 5)

        self.assertEqual(browsers[0].priority, 0)
        self.assertEqual(browsers[1].priority, 1)
        # self.assertEqual(browsers[2].priority, 2)

    def test_read_browser_setup__nonempty(self):
        Browser.objects.all().delete()

        # call tested function
        Browser.read_browser_setup()

        browsers = Browser.objects.all()
        self.assertTrue(browsers.count() > 0)

        init_value = browsers.count()

        # call again
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

    def test_get_setup__standard(self):
        Browser.objects.all().delete()

        browser = Browser.objects.create(
            name="test",
            crawler="RequestsCrawler",
            settings='{"test_setting" : "something"}',
        )

        # call tested function
        setup = browser.get_setup()
        self.assertTrue(setup["name"], "test")
        self.assertTrue(setup["crawler"], RequestsCrawler)
        self.assertTrue(setup["settings"]["test_setting"], "something")

    def test_prio_up(self):
        Browser.read_browser_setup()

        browsers = Browser.objects.all()
        self.assertTrue(browsers.count() > 5)

        first = browsers[0]
        second = browsers[1]
        # third = browsers[2]

        self.assertEqual(first.priority, 0)
        self.assertEqual(second.priority, 1)
        # self.assertEqual(third.priority, 2)

        # call tested function
        second.prio_up()

        first.refresh_from_db()
        second.refresh_from_db()
        # third.refresh_from_db()

        self.assertEqual(first.priority, 1)
        self.assertEqual(second.priority, 0)
        # self.assertEqual(third.priority, 2)

    def test_prio_down(self):
        Browser.read_browser_setup()

        browsers = Browser.objects.all()
        self.assertTrue(browsers.count() > 5)

        first = browsers[0]
        second = browsers[1]

        self.assertEqual(first.priority, 0)
        self.assertEqual(second.priority, 1)

        # call tested function
        first.prio_down()

        first.refresh_from_db()
        second.refresh_from_db()

        self.assertEqual(first.priority, 1)
        self.assertEqual(second.priority, 0)
