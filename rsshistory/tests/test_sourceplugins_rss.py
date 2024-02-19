from ..controllers import SourceDataController
from ..configuration import Configuration
from ..pluginsources.sourcerssplugin import BaseRssPlugin

from .fakeinternet import FakeInternetTestCase


class BaseRssPluginTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()
        self.setup_configuration()

        self.source_rss = SourceDataController.objects.create(
            url="https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM",
            title="SAMTIME",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )

    def test_get_container_elements(self):
        config = Configuration.get_object().config_entry
        config.auto_store_entries = True
        config.auto_store_sources = True
        config.auto_store_domain_info = False
        config.auto_store_entries_use_all_data = False
        config.auto_store_entries_use_clean_page_info = False
        config.save()

        self.mock_page_requests = 0

        self.assertTrue(self.source_rss)

        plugin = BaseRssPlugin(self.source_rss.id)
        props = plugin.get_container_elements()
        props = list(props)

        self.print_errors()

        self.assertEqual(len(props), 6)
        self.assertEqual(
            props[0]["source"],
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM",
        )

        # 1 rss parent, we do not make additional requests
        self.assertEqual(self.mock_page_requests, 1)

    def test_get_container_elements_use_all_data(self):
        config = Configuration.get_object().config_entry
        config.auto_store_entries = True
        config.auto_store_sources = True
        config.auto_store_domain_info = False
        config.auto_store_entries_use_all_data = True
        config.auto_store_entries_use_clean_page_info = False
        config.save()

        self.assertTrue(self.source_rss)

        plugin = BaseRssPlugin(self.source_rss.id)
        props = plugin.get_container_elements()
        props = list(props)

        self.print_errors()

        self.assertEqual(len(props), 6)
        self.assertEqual(
            props[0]["source"],
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM",
        )

    def test_get_container_elements_use_clean_page_info(self):
        config = Configuration.get_object().config_entry
        config.auto_store_entries = True
        config.auto_store_sources = True
        config.auto_store_domain_info = False
        config.auto_store_entries_use_all_data = False
        config.auto_store_entries_use_clean_page_info = True
        config.save()

        self.assertTrue(self.source_rss)

        plugin = BaseRssPlugin(self.source_rss.id)
        props = plugin.get_container_elements()
        props = list(props)

        self.print_errors()

        self.assertEqual(len(props), 6)
        self.assertEqual(
            props[0]["source"],
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM",
        )

    def test_check_for_data(self):
        config = Configuration.get_object().config_entry
        config.auto_store_entries = True
        config.auto_store_sources = True
        config.auto_store_domain_info = False
        config.auto_store_entries_use_all_data = True
        config.auto_store_entries_use_clean_page_info = False
        config.save()

        self.assertTrue(self.source_rss)

        plugin = BaseRssPlugin(self.source_rss.id)
        # call tested function
        plugin.check_for_data()

        self.print_errors()

        self.assertTrue(plugin.hash)
