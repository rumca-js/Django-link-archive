import json
from django.contrib.auth.models import User

from ..configuration import Configuration
from ..controllers import SourceDataController, LinkDataController
from ..pluginsources.sourcejsonplugin import BaseSourceJsonPlugin

from .fakeinternet import FakeInternetTestCase
from .fake.instance import instance_entries_source_100_json, instance_entries_json


class BaseJsonPluginTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
            is_superuser=True,
        )

    def test_get_entries__source(self):
        LinkDataController.objects.all().delete()

        self.source_obj = SourceDataController.objects.create(
            url="https://instance.com/apps/rsshistory/source-json/100",
            title="RSS history instance",
            export_to_cms=True,
        )

        plugin = BaseSourceJsonPlugin(self.source_obj.id)
        # call tested function
        props = plugin.get_entries()

        self.print_errors()

        json_obj = json.loads(instance_entries_source_100_json)

        entries = LinkDataController.objects.filter(link=json_obj["links"][0]["link"])

        self.assertEqual(entries.count(), 1)
        #self.assertEqual(entries[0].source, "https://www.lemonde.fr/en/rss/une.xml")

    def test_get_entries__links(self):
        LinkDataController.objects.all().delete()

        self.source_obj = SourceDataController.objects.create(
            url="https://instance.com/apps/rsshistory/entries-json/?query_type=recent",
            title="RSS history instance",
            export_to_cms=True,
        )

        plugin = BaseSourceJsonPlugin(self.source_obj.id)
        # call tested function
        props = plugin.get_entries()

        self.print_errors()

        json_obj = json.loads(instance_entries_json)

        entries = LinkDataController.objects.filter(link=json_obj["links"][0]["link"])

        self.assertEqual(entries.count(), 1)
        #self.assertEqual(entries[0].source, "https://www.lemonde.fr/en/rss/une.xml")

    def test_get_entries__sources(self):
        config = Configuration.get_object().config_entry
        config.accept_non_domain_links = True
        config.accept_domain_links = False
        config.new_source_enabled_state = False
        config.auto_create_sources = False

        config.save()

        LinkDataController.objects.all().delete()
        SourceDataController.objects.all().delete()

        self.source_obj = SourceDataController.objects.create(
            url="https://instance.com/apps/rsshistory/sources-json",
            title="RSS history instance",
            export_to_cms=True,
        )

        plugin = BaseSourceJsonPlugin(self.source_obj.id)
        # call tested function
        props = plugin.get_entries()

        sources = SourceDataController.objects.all().order_by("-enabled")
        for source in sources:
            print("Source:{} enabled:{}".format(source.url, source.enabled))

        # 3 imported, 1 created here in test
        self.assertEqual(sources.count(), 3 + 1)

        self.assertEqual(
            sources[0].url, "https://instance.com/apps/rsshistory/sources-json"
        )
        self.assertEqual(sources[0].enabled, True)
        self.assertEqual(sources[1].url, "https://www.lemonde.fr/en/rss/une.xml")
        self.assertEqual(sources[1].enabled, False)
        self.assertEqual(sources[2].url, "https://3dprinting.com/feed")
        self.assertEqual(sources[2].enabled, False)
        self.assertEqual(sources[3].url, "https://www.404media.co/rss")
        self.assertEqual(sources[3].enabled, False)

        self.assertEqual(
            sources[1].proxy_location,
            "https://instance.com/apps/rsshistory/source-json/100",
        )
        self.assertEqual(
            sources[2].proxy_location,
            "https://instance.com/apps/rsshistory/source-json/101",
        )
        self.assertEqual(
            sources[3].proxy_location,
            "https://instance.com/apps/rsshistory/source-json/102",
        )

        # Links are not imported
        entries = LinkDataController.objects.all()
        self.assertEqual(entries.count(), 0)
