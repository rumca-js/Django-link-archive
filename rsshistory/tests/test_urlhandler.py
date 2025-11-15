from webtoolkit import (
    RssPage,
    HtmlPage,
)
from ..models import Browser, EntryRules

from ..pluginurl.urlhandler import UrlHandler

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class UrlHandlerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_constructor__default_browsers(self):
        Browser.objects.all().delete()

        browser1 = Browser.objects.create(
            name="test1",
            settings='{"test_setting" : "something"}',
        )

        browser2 = Browser.objects.create(
            name="test2",
            settings='{"test_setting" : "something"}',
        )

        test_link = "https://rsspage.com/rss.xml"

        # call tested function
        handler = UrlHandler(test_link)

        mapping = handler.browsers

        self.assertEqual(len(mapping), 2)
        self.assertEqual(mapping[0]["name"], "test1")
        self.assertEqual(mapping[1]["name"], "test2")

    def test_constructor__default_browsers__entry_rules(self):
        Browser.objects.all().delete()

        browser1 = Browser.objects.create(
            name="test1",
            settings='{"test_setting" : "something"}',
        )

        browser2 = Browser.objects.create(
            name="test2",
            settings='{"test_setting" : "something"}',
        )

        # browser 2 is more important
        EntryRules.objects.create(
            trigger_rule_url="rsspage.com",
            browser=browser2,
        )

        test_link = "https://rsspage.com/rss.xml"

        # call tested function
        handler = UrlHandler(test_link)

        mapping = handler.browsers

        self.assertEqual(len(mapping), 2)
        self.assertEqual(mapping[0]["name"], "test2")
        self.assertEqual(mapping[1]["name"], "test1")

    def test_constructor__arg_browsers(self):
        Browser.objects.all().delete()

        browser1 = Browser.objects.create(
            name="test1",
            settings='{"test_setting" : "something"}',
        )

        browser2 = Browser.objects.create(
            name="test2",
            settings='{"test_setting" : "something"}',
        )

        test_link = "https://rsspage.com/rss.xml"

        # call tested function
        handler = UrlHandler(test_link, browsers=[browser1])

        mapping = handler.browsers

        self.assertEqual(len(mapping), 1)
        self.assertEqual(mapping[0]["name"], "test1")

    def test_get_browsers(self):
        Browser.objects.all().delete()

        browser1 = Browser.objects.create(
            name="test1",
            settings='{"test_setting" : "something"}',
        )

        browser2 = Browser.objects.create(
            name="test2",
            settings='{"test_setting" : "something"}',
        )

        test_link = "https://rsspage.com/rss.xml"

        handler = UrlHandler(test_link)

        # call tested function
        mapping = handler.get_browsers()

        self.assertEqual(len(mapping), 2)
        self.assertEqual(mapping[0]["name"], "test1")
        self.assertEqual(mapping[1]["name"], "test2")

    def test_get_ready_browser(self):
        Browser.objects.all().delete()

        browser1 = Browser.objects.create(
            name="test1",
            settings='{"test_setting" : "something"}',
        )

        browser2 = Browser.objects.create(
            name="test2",
            settings='{"test_setting" : "something"}',
        )

        test_link = "https://rsspage.com/rss.xml"

        handler = UrlHandler(
            test_link,
            browsers=[browser1, browser],
            settings={"handler_class": "HttpPageHandler"},
        )

        # call tested function
        browsers = handler.get_browsers()

        self.assertTrue(len(browsers) > 0)

        self.assertEqual(browsers[0]["name"], "test1")
        self.assertEqual(browsers[0]["settings"]["handler_class"], "HttpPageHandler")

    def test_get_properties__no_browser(self):
        Browser.objects.all().delete()
        handler = UrlHandler("https://rsspage.com/rss.xml")

        # call tested function
        properties = handler.get_properties()

        self.assertTrue(properties)

    def test_get_properties__browsers(self):
        browser1 = Browser.objects.create(
            name="test1",
            settings='{"test_setting" : "something", "timeout_s" : 20}',
        )

        browser2 = Browser.objects.create(
            name="test2",
            settings='{"test_setting" : "something", "timeout_s" : 20}',
        )

        EntryRules.objects.create(
            trigger_rule_url="https://rsspage.com",
            browser=browser1,
        )

        handler = UrlHandler("https://rsspage.com/rss.xml")

        # call tested function
        properties = handler.get_properties()

        self.assertTrue(properties)
        self.assertIn("info", MockRequestCounter.request_history[-1])
        self.assertIn("settings", MockRequestCounter.request_history[-1]["info"])

        self.assertIn(
            "test_setting", MockRequestCounter.request_history[-1]["info"]["settings"]
        )

        self.assertIn(
            "timeout_s", MockRequestCounter.request_history[-1]["info"]["settings"]
        )
        self.assertNotIn("timeout_s", MockRequestCounter.request_history[-1]["info"])

    def test_get_cleaned_link__linkedin(self):
        MockRequestCounter.mock_page_requests = 0

        # call tested function
        cleaned_link = UrlHandler.get_cleaned_link("https://linkedin.com")

        self.assertEqual(cleaned_link, "https://linkedin.com")
        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_get_cleaned_link__stupid_google_link(self):
        MockRequestCounter.mock_page_requests = 0

        # call tested function
        cleaned_link = UrlHandler.get_cleaned_link(
            "https://www.google.com/url?q=https://forum.ddopl.com/&sa=Udupa"
        )

        self.assertEqual(cleaned_link, "https://forum.ddopl.com")
        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_get_cleaned_link__stupid_google_link2(self):
        MockRequestCounter.mock_page_requests = 0

        # call tested function
        cleaned_link = UrlHandler.get_cleaned_link(
            "https://www.google.com/url?sa=t&source=web&rct=j&opi=89978449&url=https://worldofwarcraft.blizzard.com/&ved=2ahUKEwjtx56Pn5WFAxU2DhAIHYR1CckQFnoECCkQAQ&usg=AOvVaw1pDkx5K7B5loKccvg_079-"
        )

        self.assertEqual(cleaned_link, "https://worldofwarcraft.blizzard.com")
        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_get_cleaned_link__stupid_youtube_link(self):
        MockRequestCounter.mock_page_requests = 0

        # call tested function
        cleaned_link = UrlHandler.get_cleaned_link(
            "https://www.youtube.com/redirect?event=lorum&redir_token=ipsum&q=https%3A%2F%2Fcorridordigital.com%2F&v=LeB9DcFT810"
        )

        self.assertEqual(cleaned_link, "https://corridordigital.com")
        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_get_cleaned_link__youtube(self):
        MockRequestCounter.mock_page_requests = 0

        # call tested function
        cleaned_link = UrlHandler.get_cleaned_link("https://www.YouTube.com/Test")
        self.assertEqual(cleaned_link, "https://www.youtube.com/Test")

        # call tested function
        cleaned_link = UrlHandler.get_cleaned_link("https://www.YouTube.com/Test/")
        self.assertEqual(cleaned_link, "https://www.youtube.com/Test")

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_is_blocked__entry_rule(self):
        # browser 2 is more important
        EntryRules.objects.create(
            trigger_text="casino",
            block=True,
        )

        url = UrlHandler("https://linkedin.com")
        # call tested function
        self.assertFalse(url.is_blocked())

        url = UrlHandler("https://casino.com")
        # call tested function
        self.assertTrue(url.is_blocked())

    def test_get_text__valid(self):
        url = UrlHandler("https://linkedin.com")
        # call tested function
        self.assertTrue(url.get_text())

    def test_get_binary__invalid(self):
        url = UrlHandler("https://linkedin.com")
        # call tested function
        self.assertFalse(url.get_binary())

    def test_get_binary__valid(self):
        url = UrlHandler("https://binary.com/file")
        # call tested function
        self.assertTrue(url.get_binary())
