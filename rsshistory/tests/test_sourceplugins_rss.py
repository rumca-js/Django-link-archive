from ..controllers import SourceDataController, LinkDataController
from ..configuration import Configuration
from ..pluginsources.sourcerssplugin import BaseRssPlugin

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class BaseRssPluginTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()
        self.setup_configuration()

        self.source_rss = SourceDataController.objects.create(
            url="https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM",
            title="SAMTIME",
            export_to_cms=True,
        )

    def test_get_entries(self):
        LinkDataController.objects.all().delete()

        config = Configuration.get_object().config_entry
        config.accept_not_domain_entries = True
        config.auto_create_sources = True
        config.accept_domains = False
        config.new_entries_merge_data = False
        config.new_entries_use_clean_data = False
        config.save()

        MockRequestCounter.mock_page_requests = 0

        self.assertTrue(self.source_rss)

        plugin = BaseRssPlugin(self.source_rss.id)
        # call tested function
        props = plugin.get_entries()
        props = list(props)

        self.print_errors()

        self.assertEqual(len(props), 13)
        self.assertEqual(
            props[0]["source"],
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM",
        )

        # 1 rss parent, we do not make additional requests
        self.assertEqual(MockRequestCounter.mock_page_requests, 1)

    def test_get_entries__use_all_data(self):
        LinkDataController.objects.all().delete()

        config = Configuration.get_object().config_entry
        config.accept_not_domain_entries = True
        config.auto_create_sources = True
        config.accept_domains = False
        config.new_entries_merge_data = True
        config.new_entries_use_clean_data = False
        config.save()

        self.assertTrue(self.source_rss)

        plugin = BaseRssPlugin(self.source_rss.id)
        # call tested function
        props = plugin.get_entries()
        props = list(props)

        self.print_errors()

        self.assertEqual(len(props), 13)
        self.assertEqual(
            props[0]["source"],
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM",
        )

    def test_get_entries__use_clean_page_info(self):
        LinkDataController.objects.all().delete()

        config = Configuration.get_object().config_entry
        config.accept_not_domain_entries = True
        config.auto_create_sources = True
        config.accept_domains = False
        config.new_entries_merge_data = False
        config.new_entries_use_clean_data = True
        config.save()

        self.assertTrue(self.source_rss)

        plugin = BaseRssPlugin(self.source_rss.id)
        # call tested function
        props = plugin.get_entries()
        props = list(props)

        self.print_errors()

        self.assertEqual(len(props), 13)
        self.assertEqual(
            props[0]["source"],
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM",
        )

    def test_get_entries__encoded(self):
        LinkDataController.objects.all().delete()

        config = Configuration.get_object().config_entry
        config.accept_not_domain_entries = True
        config.auto_create_sources = True
        config.accept_domains = False
        config.new_entries_merge_data = False
        config.new_entries_use_clean_data = True
        config.save()

        test_link = "https://www.geekwire.com/feed"

        self.source_rss = SourceDataController.objects.create(
            url=test_link,
            title="Warhammer community",
            export_to_cms=True,
        )

        self.assertTrue(self.source_rss)

        plugin = BaseRssPlugin(self.source_rss.id)
        # call tested function
        props = plugin.get_entries()
        props = list(props)

        self.print_errors()

        self.assertEqual(len(props), 5)
        self.assertEqual(
            props[0]["source"],
            test_link
        )

    def test_check_for_data(self):
        LinkDataController.objects.all().delete()

        config = Configuration.get_object().config_entry
        config.accept_not_domain_entries = True
        config.auto_create_sources = True
        config.accept_domains = False
        config.new_entries_merge_data = True
        config.new_entries_use_clean_data = False
        config.save()

        self.assertTrue(self.source_rss)

        plugin = BaseRssPlugin(self.source_rss.id)
        # call tested function
        plugin.check_for_data()

        self.print_errors()

        self.assertTrue(plugin.hash)

    def test_calculate_plugin_hash(self):
        plugin = BaseRssPlugin(self.source_rss.id)
        self.assertTrue(plugin.calculate_plugin_hash())
