import json

from ..configuration import Configuration
from ..controllers import SourceDataController, LinkDataController
from ..pluginsources.sourcejsonplugin import BaseSourceJsonPlugin

from .fakeinternet import FakeInternetTestCase
from .fakeinternetdata import instance_entries_source_100_json,instance_entries_json


class BaseJsonPluginTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_get_link_props_source(self):
        LinkDataController.objects.all().delete()

        self.source_obj = SourceDataController.objects.create(
            url="https://instance.com/apps/rsshistory/source-json/100",
            title="RSS history instance",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )

        plugin = BaseSourceJsonPlugin(self.source_obj.id)
        props = plugin.get_link_props()

        self.print_errors()

        json_obj = json.loads(instance_entries_source_100_json)

        entries = LinkDataController.objects.filter(link = json_obj["links"][0]["link"])

        self.assertEqual(entries.count(), 1)
        self.assertEqual(entries[0].source, "https://www.lemonde.fr/en/rss/une.xml")

    def test_get_link_props_links(self):
        LinkDataController.objects.all().delete()

        self.source_obj = SourceDataController.objects.create(
            url="https://instance.com/apps/rsshistory/entries-json/?query_type=recent",
            title="RSS history instance",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )

        plugin = BaseSourceJsonPlugin(self.source_obj.id)
        props = plugin.get_link_props()

        self.print_errors()

        json_obj = json.loads(instance_entries_json)

        entries = LinkDataController.objects.filter(link = json_obj["links"][0]["link"])

        self.assertEqual(entries.count(), 1)
        self.assertEqual(entries[0].source, "https://www.lemonde.fr/en/rss/une.xml")

    def test_get_link_props_sources(self):
        config = Configuration.get_object().config_entry
        config.auto_store_entries = True
        config.auto_store_domain_info = False
        config.save()

        LinkDataController.objects.all().delete()
        SourceDataController.objects.all().delete()

        self.source_obj = SourceDataController.objects.create(
            url="https://instance.com/apps/rsshistory/sources-json",
            title="RSS history instance",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )

        plugin = BaseSourceJsonPlugin(self.source_obj.id)
        props = plugin.get_link_props()

        sources = SourceDataController.objects.all().order_by("-on_hold")
        for source in sources:
            print("Enabled source:{}".format(source.url))

        # 3 imported, 1 created here in test
        self.assertEqual(sources.count(), 3+1)

        self.assertEqual(sources[0].on_hold, True)
        self.assertEqual(sources[1].on_hold, True)
        self.assertEqual(sources[2].on_hold, True)

        self.assertEqual(sources[0].proxy_location, "https://instance.com/apps/rsshistory/source-json/100")
        self.assertEqual(sources[1].proxy_location, "https://instance.com/apps/rsshistory/source-json/101")
        self.assertEqual(sources[2].proxy_location, "https://instance.com/apps/rsshistory/source-json/102")

        self.assertEqual(sources[3].on_hold, False)

        # Links are imported
        entries = LinkDataController.objects.all()
        self.assertEqual(entries.count(), 1)
        self.assertEqual(entries[0].link, "https://www.lemonde.fr/first-link.html")
