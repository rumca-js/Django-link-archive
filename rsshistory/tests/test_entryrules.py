from datetime import timedelta
from django.contrib.auth.models import User

from utils.dateutils import DateUtils
from ..webtools import SeleniumChromeHeadless, SeleniumChromeFull

from ..controllers import (
    SourceDataController,
    LinkDataController,
    EntryUpdater,
)
from ..models import EntryRules, Browser
from ..configuration import Configuration

from .fakeinternet import FakeInternetTestCase


class EntryUpdaterTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()
        self.setup_configuration()

        self.user = User.objects.create_user(
            username="TestUser", password="testpassword", is_staff=True
        )

        self.browser = Browser.objects.create(
            name="RequestsCrawler",
            crawler="SeleniumChromeHeadless",
            settings='{"test_setting" : "something"}',
        )
        self.browser_selenium = Browser.objects.create(
            name="SeleniumChromeHeadless",
            crawler="SeleniumChromeHeadless",
            settings='{"test_setting" : "something"}',
        )
        self.browser.refresh_from_db()

    def test_entry_rule_is_blocked__not_filed(self):
        EntryRules.objects.create(
            enabled=True,
            block=True,
            rule_name="Rule1",
            trigger_rule_url=".test1.com, .test2.com",
        )
        EntryRules.objects.create(
            enabled=True,
            block=True,
            rule_name="Rule2",
            trigger_rule_url=".test3.com, .test4.com",
        )

        # call tested function
        self.assertFalse(EntryRules.is_blocked("https://www.test0.com"))
        # call tested function
        self.assertTrue(EntryRules.is_blocked("https://www.test1.com"))
        # call tested function
        self.assertTrue(EntryRules.is_blocked("https://www.test2.com"))
        # call tested function
        self.assertTrue(EntryRules.is_blocked("https://www.test3.com"))
        # call tested function
        self.assertTrue(EntryRules.is_blocked("https://www.test4.com"))
        # call tested function
        self.assertFalse(EntryRules.is_blocked("https://www.test5.com"))

    def test_entry_rule_is_blocked__rules_disabled(self):
        EntryRules.objects.create(
            enabled=True,
            block=False,
            rule_name="Rule1",
            trigger_rule_url=".test1.com, .test2.com",
        )
        EntryRules.objects.create(
            enabled=True,
            block=False,
            rule_name="Rule2",
            trigger_rule_url=".test3.com, .test4.com",
        )

        # call tested function
        self.assertFalse(EntryRules.is_blocked("https://www.test0.com"))
        # call tested function
        self.assertFalse(EntryRules.is_blocked("https://www.test1.com"))
        # call tested function
        self.assertFalse(EntryRules.is_blocked("https://www.test2.com"))
        # call tested function
        self.assertFalse(EntryRules.is_blocked("https://www.test3.com"))
        # call tested function
        self.assertFalse(EntryRules.is_blocked("https://www.test4.com"))
        # call tested function
        self.assertFalse(EntryRules.is_blocked("https://www.test5.com"))

    def test_entry_rule_is_blocked_by_text(self):
        EntryRules.objects.create(
            enabled=True,
            block=True,
            rule_name="Rule1",
            trigger_text="casino",
        )

        text = "casino casino casino"

        # call tested function
        self.assertFalse(EntryRules.is_blocked_by_text(text))

        text = "casino casino casino casino"

        # call tested function
        self.assertTrue(EntryRules.is_blocked_by_text(text))

    def test_entry_rule__get_url_rules(self):

        self.browser.save()

        therule = EntryRules.objects.create(
            enabled=True,
            block=False,
            browser=self.browser,
            rule_name="Rule1",
            trigger_rule_url=".test1.com, .test2.com",
        )

        # call tested function
        rules0 = EntryRules.get_url_rules("https://www.test0.com")
        # call tested function
        rules1 = EntryRules.get_url_rules("https://www.test1.com")
        # call tested function
        rules2 = EntryRules.get_url_rules("https://www.test2.com")
        # call tested function
        rules3 = EntryRules.get_url_rules("https://www.test3.com")

        # call tested function
        self.assertEqual(len(rules0), 0)
        self.assertEqual(len(rules1), 1)
        self.assertEqual(len(rules2), 1)
        self.assertEqual(len(rules3), 0)

        self.assertEqual(rules1[0], therule)
        self.assertEqual(rules2[0], therule)

    def test_entry_rule__is_valid(self):

        self.browser.save()

        therule = EntryRules.objects.create(
            enabled=True,
            block=False,
            browser=self.browser,
            rule_name="Rule1",
            trigger_rule_url=".test1.com, .test2.com",
        )

        self.assertTrue(therule.is_valid())

    def test_is_entry_blocked(self):

        self.browser.save()

        therule = EntryRules.objects.create(
            enabled=True,
            block=True,
            rule_name="Rule1",
            trigger_rule_url=".test1.com, .test2.com",
        )

        entry = LinkDataController.objects.create(link = "https://something.test1.com")

        self.assertTrue(EntryRules.is_entry_blocked(entry))
