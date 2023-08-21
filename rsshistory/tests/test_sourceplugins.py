from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from ..controllers import SourceDataController
from ..pluginsources.sourcerssplugin import BaseRssPlugin
from ..pluginsources.sourceparseplugin import BaseParsePlugin
from ..pluginsources.sourcegenerousparserplugin import SourceGenerousParserPlugin
from ..pluginsources.sourceparseditigsplugin import SourceParseDigitsPlugin


class SourceParsePluginTest(TestCase):

    def setUp(self):
        self.source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )

    def test_is_link_valid_html(self):
        parse = BaseParsePlugin(self.source_youtube)
        self.assertTrue(parse.is_link_valid("https://youtube.com/location/inside.html"))

    def test_is_link_valid_htm(self):
        parse = BaseParsePlugin(self.source_youtube)
        self.assertTrue(parse.is_link_valid("https://youtube.com/location/inside.htm"))

    def test_is_link_valid_ending_dash(self):
        parse = BaseParsePlugin(self.source_youtube)
        self.assertTrue(parse.is_link_valid("https://youtube.com/location/inside/"))

    def test_is_link_valid_ending_noext(self):
        parse = BaseParsePlugin(self.source_youtube)
        self.assertTrue(parse.is_link_valid("https://youtube.com/location/inside"))

    # check if false

    def test_is_link_valid_outside_location(self):
        parse = BaseParsePlugin(self.source_youtube)
        self.assertFalse(parse.is_link_valid("https://github.com/location/inside"))

    def test_is_link_valid_js(self):
        parse = BaseParsePlugin(self.source_youtube)
        self.assertFalse(parse.is_link_valid("https://youtube.com/location/inside.js"))

    def test_is_link_valid_css(self):
        parse = BaseParsePlugin(self.source_youtube)
        self.assertFalse(parse.is_link_valid("https://youtube.com/location/inside.css"))


class SourceGenerousParsePluginTest(TestCase):

    def setUp(self):
        self.source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )

    def test_is_link_valid_html(self):
        parse = SourceGenerousParserPlugin(self.source_youtube)
        self.assertTrue(parse.is_link_valid("https://youtube.com/location/inside.html"))

    def test_is_link_valid_htm(self):
        parse = SourceGenerousParserPlugin(self.source_youtube)
        self.assertTrue(parse.is_link_valid("https://youtube.com/location/inside.htm"))

    def test_is_link_valid_ending_dash(self):
        parse = SourceGenerousParserPlugin(self.source_youtube)
        self.assertTrue(parse.is_link_valid("https://youtube.com/location/inside/"))

    def test_is_link_valid_ending_noext(self):
        parse = SourceGenerousParserPlugin(self.source_youtube)
        self.assertTrue(parse.is_link_valid("https://youtube.com/location/inside"))

    # check if false

    def test_is_link_valid_outside_location(self):
        parse = SourceGenerousParserPlugin(self.source_youtube)
        self.assertFalse(parse.is_link_valid("https://github.com/location/inside"))

    def test_is_link_valid_js(self):
        parse = SourceGenerousParserPlugin(self.source_youtube)
        self.assertFalse(parse.is_link_valid("https://youtube.com/location/inside.js"))

    def test_is_link_valid_css(self):
        parse = SourceGenerousParserPlugin(self.source_youtube)
        self.assertFalse(parse.is_link_valid("https://youtube.com/location/inside.css"))

