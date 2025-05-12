from datetime import timedelta
from django.contrib.auth.models import User

from utils.dateutils import DateUtils
from ..webtools import SeleniumChromeHeadless, SeleniumChromeFull

from ..controllers import (
    SourceDataController,
    LinkDataController,
    EntryUpdater,
)
from ..models import EntryRules, Browser, UserBookmarks
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

    def test_is_url_blocked__not_filed(self):
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
        self.assertFalse(EntryRules.is_url_blocked("https://www.test0.com"))
        # call tested function
        self.assertTrue(EntryRules.is_url_blocked("https://www.test1.com"))
        # call tested function
        self.assertTrue(EntryRules.is_url_blocked("https://www.test2.com"))
        # call tested function
        self.assertTrue(EntryRules.is_url_blocked("https://www.test3.com"))
        # call tested function
        self.assertTrue(EntryRules.is_url_blocked("https://www.test4.com"))
        # call tested function
        self.assertFalse(EntryRules.is_url_blocked("https://www.test5.com"))

    def test_is_url_blocked__rules_disabled(self):
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
        self.assertFalse(EntryRules.is_url_blocked("https://www.test0.com"))
        # call tested function
        self.assertFalse(EntryRules.is_url_blocked("https://www.test1.com"))
        # call tested function
        self.assertFalse(EntryRules.is_url_blocked("https://www.test2.com"))
        # call tested function
        self.assertFalse(EntryRules.is_url_blocked("https://www.test3.com"))
        # call tested function
        self.assertFalse(EntryRules.is_url_blocked("https://www.test4.com"))
        # call tested function
        self.assertFalse(EntryRules.is_url_blocked("https://www.test5.com"))

    def test_is_text_triggered__nocomma(self):
        EntryRules.objects.all().delete()

        rule = EntryRules.objects.create(
            enabled=True,
            block=True,
            rule_name="Rule1",
            trigger_text="casino",
            trigger_text_hits=4,
        )

        text = "casino casino casino"

        # call tested function
        self.assertFalse(rule.is_text_triggered(text))

        text = "casino casino casino casino"

        # call tested function
        self.assertTrue(rule.is_text_triggered(text))

    def test_is_text_triggered__comma(self):
        EntryRules.objects.all().delete()

        rule = EntryRules.objects.create(
            enabled=True,
            block=True,
            rule_name="Rule1",
            trigger_text="casino, royale",
            trigger_text_hits=4,
        )

        text = "casino casino casino"

        # call tested function
        self.assertFalse(rule.is_text_triggered(text))

        text = "casino casino casino casino"

        # call tested function
        self.assertTrue(rule.is_text_triggered(text))

    def test_is_text_triggered__2commas(self):
        EntryRules.objects.all().delete()

        rule = EntryRules.objects.create(
            enabled=True,
            block=True,
            rule_name="Rule1",
            trigger_text="casino, royale,",
            trigger_text_hits=4,
        )

        text = "casino casino casino"

        # call tested function
        self.assertFalse(rule.is_text_triggered(text))

        text = "casino casino casino casino"

        # call tested function
        self.assertTrue(rule.is_text_triggered(text))

    def test_get_url_rules(self):

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

    def test_is_valid(self):

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

        entry = LinkDataController.objects.create(link="https://something.test1.com")

        self.assertTrue(EntryRules.is_entry_blocked(entry))

    def test_get_age_for_dictionary(self):

        self.browser.save()

        therule = EntryRules.objects.create(
            enabled=True,
            block=False,
            rule_name="Rule1",
            trigger_text="nsfw",
            trigger_text_hits=1,
            apply_age_limit=15,
        )

        dictionary = {
            "title": "AI girlfriend NSFW",
            "description": "",
        }

        self.assertEqual(EntryRules.get_age_for_dictionary(dictionary), 15)

    def test_apply_entry_rule__applies_age(self):

        therule = EntryRules.objects.create(
            enabled=True,
            block=False,
            rule_name="Rule1",
            trigger_text="nsfw",
            trigger_text_hits=1,
            apply_age_limit=15,
        )

        entry = LinkDataController.objects.create(
            link="https://nsfw.com",
            title="NFSW AI girlfriend",
            description="NSFW AI girlfriend",
        )

        # call tested function
        EntryRules.apply_entry_rule(entry)

        entry.refresh_from_db()

        self.assertEqual(entry.age, 15)

    def test_check_all__removes(self):

        therule = EntryRules.objects.create(
            enabled=True,
            block=True,
            rule_name="Rule1",
            trigger_text="nsfw",
            trigger_text_hits=1,
        )

        entry = LinkDataController.objects.create(
            link="https://nsfw.com",
            title="NFSW AI girlfriend",
            description="NSFW AI girlfriend",
        )

        # call tested function
        EntryRules.check_all(entry)

        entries = LinkDataController.objects.filter(link="https://nsfw.com")
        self.assertEqual(len(entries), 0)

    def test_check_all__does_not_remove_bookmarked(self):

        therule = EntryRules.objects.create(
            enabled=True,
            block=True,
            rule_name="Rule1",
            trigger_text="nsfw",
            trigger_text_hits=1,
        )

        entry = LinkDataController.objects.create(
            link="https://nsfw.com",
            title="NFSW AI girlfriend",
            description="NSFW AI girlfriend",
            bookmarked=True,
        )

        UserBookmarks.add(self.user, entry)

        # call tested function
        EntryRules.check_all(entry)

        entries = LinkDataController.objects.filter(link="https://nsfw.com")
        self.assertEqual(len(entries), 1)

    def test_get_entry_pulp__empty_fields(self):

        self.browser.save()

        therule = EntryRules.objects.create(
            enabled=True,
            block=False,
            rule_name="Rule1",
            trigger_text="nsfw",
            trigger_text_hits=1,
            apply_age_limit=15,
        )

        entry = LinkDataController.objects.create(
            link="https://nsfw.com",
            title="NFSW AI girlfriend - title",
            description="NSFW AI girlfriend - description",
        )

        pulp = therule.get_entry_pulp(entry)

        self.assertEqual(
            pulp, "nfsw ai girlfriend - titlensfw ai girlfriend - description"
        )

    def test_get_entry_pulp__title_field(self):

        self.browser.save()

        therule = EntryRules.objects.create(
            enabled=True,
            block=False,
            rule_name="Rule1",
            trigger_text="nsfw",
            trigger_text_hits=1,
            trigger_text_fields="title",
            apply_age_limit=15,
        )

        entry = LinkDataController.objects.create(
            link="https://nsfw.com",
            title="NFSW AI girlfriend - title",
            description="NSFW AI girlfriend - description",
        )

        pulp = therule.get_entry_pulp(entry)

        self.assertEqual(pulp, "nfsw ai girlfriend - title")

    def test_get_entry_pulp__title_description_fields(self):

        self.browser.save()

        therule = EntryRules.objects.create(
            enabled=True,
            block=False,
            rule_name="Rule1",
            trigger_text="nsfw",
            trigger_text_hits=1,
            trigger_text_fields="description, title",
            apply_age_limit=15,
        )

        entry = LinkDataController.objects.create(
            link="https://nsfw.com",
            title="NFSW AI girlfriend - title",
            description="NSFW AI girlfriend - description",
        )

        pulp = therule.get_entry_pulp(entry)

        self.assertEqual(
            pulp, "nfsw ai girlfriend - titlensfw ai girlfriend - description"
        )

    def test_get_dict_pulp(self):

        self.browser.save()

        therule = EntryRules.objects.create(
            enabled=True,
            block=False,
            rule_name="Rule1",
            trigger_text="nsfw",
            trigger_text_hits=1,
            apply_age_limit=15,
        )

        dictionary = {
            "link": "https://test.com",
            "title": "Title",
            "description": "Description",
        }

        pulp = therule.get_dict_pulp(dictionary)

        self.assertEqual(pulp, "titledescription")
