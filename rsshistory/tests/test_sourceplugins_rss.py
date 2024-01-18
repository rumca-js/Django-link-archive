
from ..controllers import SourceDataController
from ..configuration import Configuration
from ..pluginsources.sourcerssplugin import BaseRssPlugin

from .fakeinternet import FakeInternetTestCase


webpage_youtube_contents = """
<html>
<body>
   <a href="https://linkedin.com/1">Test1</a>
   <a href="https://linkedin.com/2">Test2</a>
</body>
</html>
"""

webpage_contents = """
<html>
<body>
   <a href="https://test1.com">Test1</a>
   <a href="https://test2.com">Test2</a>
</body>
</html>
"""


class BaseRssPluginTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.source_rss = SourceDataController.objects.create(
            url="https://youtube.com/channel/samtime/rss.xml",
            title="SAMTIME",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )

    def test_get_link_props(self):
        config = Configuration.get_object().config_entry
        config.auto_store_entries_use_all_data = False
        config.auto_store_entries_use_clean_page_info = False
        config.save()

        plugin = BaseRssPlugin(self.source_rss.id)
        props = plugin.get_link_props()
        props = list(props)

        self.assertEqual(len(props), 13)
        self.assertEqual(props[0]["source"], "https://youtube.com/channel/samtime/rss.xml")

    def test_get_link_props_use_all_data(self):
        config = Configuration.get_object().config_entry
        config.auto_store_entries_use_all_data = True
        config.auto_store_entries_use_clean_page_info = False
        config.save()

        plugin = BaseRssPlugin(self.source_rss.id)
        props = plugin.get_link_props()
        props = list(props)

        self.assertEqual(len(props), 13)
        self.assertEqual(props[0]["source"], "https://youtube.com/channel/samtime/rss.xml")

    def test_get_link_props_use_clean_page_info(self):
        config = Configuration.get_object().config_entry
        config.auto_store_entries_use_all_data = False
        config.auto_store_entries_use_clean_page_info = True
        config.save()

        plugin = BaseRssPlugin(self.source_rss.id)
        props = plugin.get_link_props()
        props = list(props)

        self.assertEqual(len(props), 13)
        self.assertEqual(props[0]["source"], "https://youtube.com/channel/samtime/rss.xml")
