from django.contrib.auth.models import User

from ..models import UserTags, SourceOperationalData
from ..controllers import (
    SourceDataController,
    LinkDataController,
    BackgroundJobController,
)
from ..configuration import Configuration

from ..pluginsources import BaseParsePlugin
from ..pluginsources import RssParserPlugin
from ..pluginsources import HackerNewsParserPlugin

from .fakeinternet import FakeInternetTestCase


class BaseParsePluginTest(FakeInternetTestCase):
    def setUp(self):
        self.source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            export_to_cms=True,
        )
        self.disable_web_pages()
        self.setup_configuration()

        self.user = User.objects.create_user(
            username="test_username", password="testpassword", is_superuser=True
        )

    def test_is_link_valid_html(self):
        plugin = BaseParsePlugin(self.source_youtube.id)
        self.assertTrue(plugin.is_link_valid("https://youtube.com/location/inside.html"))

    def test_is_link_valid_htm(self):
        plugin = BaseParsePlugin(self.source_youtube.id)
        self.assertTrue(plugin.is_link_valid("https://youtube.com/location/inside.htm"))

    def test_is_link_valid_ending_dash(self):
        plugin = BaseParsePlugin(self.source_youtube.id)
        self.assertTrue(plugin.is_link_valid("https://youtube.com/location/inside/"))

    def test_is_link_valid_ending_noext(self):
        plugin = BaseParsePlugin(self.source_youtube.id)
        self.assertTrue(plugin.is_link_valid("https://youtube.com/location/inside"))

    # check if false

    def test_is_link_valid_outside_location(self):
        plugin = BaseParsePlugin(self.source_youtube.id)
        self.assertTrue(plugin.is_link_valid("https://github.com/location/inside"))

    def test_is_link_valid_js(self):
        plugin = BaseParsePlugin(self.source_youtube.id)
        self.assertFalse(plugin.is_link_valid("https://youtube.com/location/inside.js"))

    def test_is_link_valid_css(self):
        plugin = BaseParsePlugin(self.source_youtube.id)
        self.assertFalse(plugin.is_link_valid("https://youtube.com/location/inside.css"))

    def test_get_hash(self):
        plugin = BaseParsePlugin(self.source_youtube.id)
        plugin.get_contents()
        self.assertTrue(plugin.get_hash())


class RssParserPluginTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.source_youtube = SourceDataController.objects.create(
            url="https://hnrss.org/frontpage",
            title="YouTube",
            export_to_cms=True,
        )

    def test_is_props_valid(self):
        parser = RssParserPlugin(self.source_youtube.id)

        # call tested function
        props = list(parser.get_entries())

        self.assertEqual(len(props), 20)

        jobs = BackgroundJobController.objects.filter(
            job=BackgroundJobController.JOB_LINK_ADD
        ).values_list("subject", flat=True)

        self.assertTrue(jobs.count() > 0)

    def test_get_hash(self):
        plugin = RssParserPlugin(self.source_youtube.id)
        plugin.get_contents()
        self.assertTrue(plugin.get_hash())


class HackerNewsParserPluginTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.source = SourceDataController.objects.create(
            url="https://hnrss.org/frontpage",
            title="YouTube",
            export_to_cms=True,
        )

        conf = Configuration.get_object().config_entry
        conf.auto_scan_new_entries = True
        conf.save()

    def is_domain(self, alist, value):
        if alist is None:
            return False

        for avalue in alist:
            if avalue["link"] == value:
                return True

        return False

    def test_is_props_valid(self):
        parser = HackerNewsParserPlugin(self.source.id)

        # call tested function
        props = list(parser.get_entries())

        # for prop in props:
        #    print(prop["link"])

        self.assertEqual(len(props), 20)

        self.assertEqual(props[0]["source"], "https://hnrss.org/frontpage")

        jobs = BackgroundJobController.objects.filter(
            job=BackgroundJobController.JOB_LINK_SCAN
        )

        self.assertEqual(jobs.count(), len(props))

    def test_get_hash(self):
        plugin = HackerNewsParserPlugin(self.source.id)
        plugin.get_contents()
        self.assertTrue(plugin.get_hash())
