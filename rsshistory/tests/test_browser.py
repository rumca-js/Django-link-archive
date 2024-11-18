from ..models import Browser

from .fakeinternet import FakeInternetTestCase


class BrowserTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_read_browser_setup(self):
        Browser.objects.all().delete()

        # call tested function
        Browser.read_browser_setup()

        browsers = Browser.objects.all()
        self.assertTrue(browsers.count() > 0)

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
                crawler = "crawler",
                settings = '{"test_setting" : "something"}',
        )

        # call tested function
        setup = browser.get_setup()
        self.assertTrue(setup["name"], "test")
        self.assertTrue(setup["crawler"], "crawler")
        self.assertTrue(setup["settings"]["test_setting"], "something")
