from ..controllers import SourceDataController
from ..pluginsources.sourceparseplugin import BaseParsePlugin
from ..pluginsources.sourcegenerousparserplugin import SourceGenerousParserPlugin
from ..pluginsources.domainparserplugin import DomainParserPlugin

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


class SourceParsePluginTest(FakeInternetTestCase):
    def setUp(self):
        self.source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )
        self.disable_web_pages()

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


class SourceGenerousParsePluginTest(FakeInternetTestCase):
    def setUp(self):
        self.source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )
        self.disable_web_pages()

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


class DomainParsePluginTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )

    def is_domain(self, alist, value):
        if alist is None:
            return False

        for avalue in alist:
            if avalue["link"] == value:
                return True

        return False

    def test_is_props_valid(self):
        parser = DomainParserPlugin(self.source_youtube.id)
        parser.contents = webpage_contents

        props = list(parser.get_container_elements())
        print(props)

        self.assertEqual(len(props), 2)

        self.assertTrue(self.is_domain(props, "https://test1.com"))
        self.assertTrue(self.is_domain(props, "https://test2.com"))

        self.assertEqual(props[0]["source"], "https://youtube.com")


class BaseParsePluginTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.source_youtube = SourceDataController.objects.create(
            url="https://linkedin.com",
            title="linkedin",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )

    def is_domain(self, alist, value):
        for avalue in alist:
            if avalue["link"] == value:
                return True

        return False

    def test_is_props_valid(self):
        parser = BaseParsePlugin(self.source_youtube.id)

        parser.contents = webpage_youtube_contents

        props = list(parser.get_container_elements())
        print(props)

        self.assertEqual(len(props), 2)

        self.assertTrue(self.is_domain(props, "https://linkedin.com/1"))
        self.assertTrue(self.is_domain(props, "https://linkedin.com/2"))

        self.assertEqual(props[0]["source"], "https://linkedin.com")
