from datetime import timedelta
from django.contrib.auth.models import User

from ..controllers import (
    SourceDataController,
    LinkDataController,
    EntryUpdater,
)
from ..models import EntryRule
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

    def test_entry_rule_get_blocked_urls__filed(self):
        EntryRule.objects.create(
                enabled=True,
                block=True,
                rule_name = "Rule1",
                rule_url = ".test1.com, .test2.com",
        )
        EntryRule.objects.create(
                enabled=True,
                block=True,
                rule_name = "Rule2",
                rule_url = ".test3.com, .test4.com",
        )

        # call tested function
        urls = EntryRule.get_blocked_urls()

        self.assertEqual(len(urls), 4)
        self.assertTrue(".test1.com" in urls)
        self.assertTrue(".test2.com" in urls)
        self.assertTrue(".test3.com" in urls)
        self.assertTrue(".test4.com" in urls)

    def test_entry_rule_get_blocked_urls__not_filed(self):
        EntryRule.objects.create(
                enabled=True,
                block=False,
                rule_name = "Rule1",
                rule_url = ".test1.com, .test2.com",
        )
        EntryRule.objects.create(
                enabled=True,
                block=False,
                rule_name = "Rule2",
                rule_url = ".test3.com, .test4.com",
        )

        # call tested function
        urls = EntryRule.get_blocked_urls()

        self.assertEqual(len(urls), 0)
