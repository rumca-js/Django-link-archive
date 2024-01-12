from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
import json

from ..controllers import SourceDataController, LinkDataController
from ..pluginsources.sourcejsonplugin import BaseSourceJsonPlugin
from .utilities import WebPageDisabled, instance_entries_source_100_json,instance_entries_json


class BaseJsonPluginTest(WebPageDisabled, TestCase):
    def setUp(self):

        self.disable_web_pages()

    def test_get_link_props_sources(self):
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
