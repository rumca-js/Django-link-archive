from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from ..controllers import SourceDataController
from ..pluginsources.sourcerssplugin import BaseRssPlugin
from ..pluginsources.sourcegenerousparserplugin import SourceGenerousParserPlugin
from ..pluginsources.sourceparseditigsplugin import SourceParseDigitsPlugin


class SourcePluginsTest(TestCase):
    pass

    # def test_rss_parser(self):
    #    source = SourceDataController.objects.create(
    #        url="https://www.youtube.com/feeds/videos.xml?channel_id=UCXGgrKt94gR6lmN4aN3mYTg"
    #    )

    #    plugin = BaseRssPlugin(source)
    #    links = plugin.get_link_props()

    #    self.assertGreater(len(links), 1)

    # def test_generous_parse(self):
    #    source = SourceDataController.objects.create(url="https://pluralistic.net/feed")

    #    plugin = SourceParseDigitsPlugin(source)
    #    links = plugin.get_link_props()

    #    self.assertGreater(len(links), 1)
