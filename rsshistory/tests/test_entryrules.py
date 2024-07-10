from datetime import timedelta
from django.contrib.auth.models import User

from ..controllers import (
    SourceDataController,
    LinkDataController,
    EntryUpdater,
)
from ..models import EntryRules
from ..configuration import Configuration
from ..dateutils import DateUtils

from .fakeinternet import FakeInternetTestCase


class EntryUpdaterTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()
        self.setup_configuration()

        self.user = User.objects.create_user(
            username="TestUser", password="testpassword", is_staff=True
        )

    def test_entry_rule_is_blocked__not_filed(self):
        EntryRules.objects.create(
            enabled=True,
            block=True,
            rule_name="Rule1",
            rule_url=".test1.com, .test2.com",
        )
        EntryRules.objects.create(
            enabled=True,
            block=True,
            rule_name="Rule2",
            rule_url=".test3.com, .test4.com",
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
            rule_url=".test1.com, .test2.com",
        )
        EntryRules.objects.create(
            enabled=True,
            block=False,
            rule_name="Rule2",
            rule_url=".test3.com, .test4.com",
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

    def test_entry_rule_is_headless_browser_required(self):
        EntryRules.objects.create(
            enabled=True,
            block=False,
            requires_headless = True,
            rule_name="Rule1",
            rule_url=".test1.com, .test2.com",
        )

        # call tested function
        self.assertFalse(EntryRules.is_headless_browser_required("https://www.test0.com"))
        # call tested function
        self.assertTrue(EntryRules.is_headless_browser_required("https://www.test1.com"))
        # call tested function
        self.assertTrue(EntryRules.is_headless_browser_required("https://www.test2.com"))
        # call tested function
        self.assertFalse(EntryRules.is_headless_browser_required("https://www.test3.com"))

    def test_entry_rule_is_full_browser_required(self):
        EntryRules.objects.create(
            enabled=True,
            block=False,
            requires_full_browser = True,
            rule_name="Rule1",
            rule_url=".test1.com, .test2.com",
        )

        # call tested function
        self.assertFalse(EntryRules.is_full_browser_required("https://www.test0.com"))
        # call tested function
        self.assertTrue(EntryRules.is_full_browser_required("https://www.test1.com"))
        # call tested function
        self.assertTrue(EntryRules.is_full_browser_required("https://www.test2.com"))
        # call tested function
        self.assertFalse(EntryRules.is_full_browser_required("https://www.test3.com"))
