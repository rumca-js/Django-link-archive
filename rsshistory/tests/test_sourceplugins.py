from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from ..controllers import SourceDataController
from ..pluginsources.sourcerssplugin import BaseRssPlugin
from ..pluginsources.sourceparseplugin import BaseParsePlugin
from ..pluginsources.sourcegenerousparserplugin import SourceGenerousParserPlugin
from ..pluginsources.sourceparseditigsplugin import SourceParseDigitsPlugin
from ..pluginsources.domainparserplugin import DomainParserPlugin



class RequestsObject(object):
    def __init__(self, url, headers, timeout):
        self.status_code = 200
        self.apparent_encoding = "utf-8"
        self.encoding = "utf-8"
        self.text = "text"
        self.content = "text"

webpage_youtube_contents = """
<html>
<body>
   <a href="https://youtube.com/1">Test1</a>
   <a href="https://youtube.com/2">Test2</a>
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
        parse = BaseParsePlugin(self.source_youtube.id)
        self.assertTrue(parse.is_link_valid("https://youtube.com/location/inside.html"))

    def test_is_link_valid_htm(self):
        parse = BaseParsePlugin(self.source_youtube.id)
        self.assertTrue(parse.is_link_valid("https://youtube.com/location/inside.htm"))

    def test_is_link_valid_ending_dash(self):
        parse = BaseParsePlugin(self.source_youtube.id)
        self.assertTrue(parse.is_link_valid("https://youtube.com/location/inside/"))

    def test_is_link_valid_ending_noext(self):
        parse = BaseParsePlugin(self.source_youtube.id)
        self.assertTrue(parse.is_link_valid("https://youtube.com/location/inside"))

    # check if false

    def test_is_link_valid_outside_location(self):
        parse = BaseParsePlugin(self.source_youtube.id)
        self.assertFalse(parse.is_link_valid("https://github.com/location/inside"))

    def test_is_link_valid_js(self):
        parse = BaseParsePlugin(self.source_youtube.id)
        self.assertFalse(parse.is_link_valid("https://youtube.com/location/inside.js"))

    def test_is_link_valid_css(self):
        parse = BaseParsePlugin(self.source_youtube.id)
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
        parse = SourceGenerousParserPlugin(self.source_youtube.id)
        self.assertTrue(parse.is_link_valid("https://youtube.com/location/inside.html"))

    def test_is_link_valid_htm(self):
        parse = SourceGenerousParserPlugin(self.source_youtube.id)
        self.assertTrue(parse.is_link_valid("https://youtube.com/location/inside.htm"))

    def test_is_link_valid_ending_dash(self):
        parse = SourceGenerousParserPlugin(self.source_youtube.id)
        self.assertTrue(parse.is_link_valid("https://youtube.com/location/inside/"))

    def test_is_link_valid_ending_noext(self):
        parse = SourceGenerousParserPlugin(self.source_youtube.id)
        self.assertTrue(parse.is_link_valid("https://youtube.com/location/inside"))

    # check if false

    def test_is_link_valid_outside_location(self):
        parse = SourceGenerousParserPlugin(self.source_youtube.id)
        self.assertFalse(parse.is_link_valid("https://github.com/location/inside"))

    def test_is_link_valid_js(self):
        parse = SourceGenerousParserPlugin(self.source_youtube.id)
        self.assertFalse(parse.is_link_valid("https://youtube.com/location/inside.js"))

    def test_is_link_valid_css(self):
        parse = SourceGenerousParserPlugin(self.source_youtube.id)
        self.assertFalse(parse.is_link_valid("https://youtube.com/location/inside.css"))



class DomainParsePluginTest(TestCase):
    def setUp(self):
        self.source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )

        self.disable_web_pages()

    def get_contents_function(self, url, headers, timeout):
        print("Mocked Requesting page: {}".format(url))
        return RequestsObject(url, headers, timeout)

    def disable_web_pages(self):
        from ..webtools import BasePage, HtmlPage

        BasePage.get_contents_function = self.get_contents_function
        HtmlPage.get_contents_function = self.get_contents_function

    def is_domain(self, alist, value):
        for avalue in alist:
            if avalue["link"] == value:
                return True

        return False

    def test_is_props_valid(self):
        parser = DomainParserPlugin(self.source_youtube.id)

        parser.contents = webpage_contents
        #domains = parser.get_domains()

        props = parser.get_link_props()
        print(props)
        
        self.assertTrue( self.is_domain(props, "https://test1.com"))
        self.assertTrue( self.is_domain(props, "https://test2.com"))


class BaseParsePluginTest(TestCase):
    def setUp(self):
        self.source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )
        self.disable_web_pages()

    def get_contents_function(self, url, headers, timeout):
        print("Mocked Requesting page: {}".format(url))
        return RequestsObject(url, headers, timeout)

    def disable_web_pages(self):
        from ..webtools import BasePage, HtmlPage

        BasePage.get_contents_function = self.get_contents_function
        HtmlPage.get_contents_function = self.get_contents_function

    def is_domain(self, alist, value):
        for avalue in alist:
            if avalue["link"] == value:
                return True

        return False

    def test_is_props_valid(self):
        parser = BaseParsePlugin(self.source_youtube.id)

        parser.contents = webpage_youtube_contents
        #domains = parser.get_domains()

        props = parser.get_link_props()
        print(props)
        
        self.assertTrue( self.is_domain(props, "https://youtube.com/1"))
        self.assertTrue( self.is_domain(props, "https://youtube.com/2"))
