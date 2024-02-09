from ..models import LinkTagsDataModel
from ..controllers import SourceDataController, LinkDataController
from ..pluginsources.sourceparseplugin import BaseParsePlugin
from ..pluginsources.sourcegenerousparserplugin import SourceGenerousParserPlugin
from ..pluginsources.domainparserplugin import DomainParserPlugin
from ..pluginsources.nownownowparserplugin import NowNowNowParserPlugin

from .fakeinternet import FakeInternetTestCase


webpage_linkedin_contents = """
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
        self.setup_configuration()

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

        # call tested function
        props = list(parser.get_container_elements())
        print(props)

        self.assertEqual(len(props), 2)

        self.assertTrue(self.is_domain(props, "https://test1.com"))
        self.assertTrue(self.is_domain(props, "https://test2.com"))

        self.assertEqual(props[0]["source"], "https://youtube.com")


webpage_linkedin_contents = """
<html>
<body>
   <a href="https://linkedin.com/1">Test1</a>
   <a href="https://linkedin.com/2">Test2</a>
</body>
</html>
"""


class BaseParsePluginTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.source_linkedin = SourceDataController.objects.create(
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
        parser = BaseParsePlugin(self.source_linkedin.id)

        parser.contents = webpage_linkedin_contents

        # call tested function
        props = list(parser.get_container_elements())
        print(props)

        self.assertEqual(len(props), 2)

        self.assertTrue(self.is_domain(props, "https://linkedin.com/1"))
        self.assertTrue(self.is_domain(props, "https://linkedin.com/2"))

        self.assertEqual(props[0]["source"], "https://linkedin.com")


webpage_linkedin_contents2 = """
<html>
<body>
   <a href="https://youtube.com/1">Test1</a>
   <a href="https://tiktok.com/2">Test2</a>
</body>
</html>
"""

class NowNowNowPluginTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()
        self.setup_configuration()

        self.source_linkedin = SourceDataController.objects.create(
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

    def is_link(self, value):
        entries = LinkDataController.objects.all()

        for entry in entries:
            if value == entry.link:
                return True

        return False

    def test_is_props_valid(self):
        parser = NowNowNowParserPlugin(self.source_linkedin.id)

        parser.contents = webpage_linkedin_contents2

        # call tested function
        props = list(parser.get_container_elements())
        print("Props: {}".format(props))

        self.print_errors()

        self.assertEqual(len(props), 2)

        self.assertTrue(self.is_domain(props, "https://youtube.com"))
        self.assertTrue(self.is_domain(props, "https://tiktok.com"))

        self.assertEqual(props[0]["source"], "https://linkedin.com")

    def test_check_for_data(self):
        LinkDataController.objects.all().delete()
        LinkTagsDataModel.objects.all().delete()

        parser = NowNowNowParserPlugin(self.source_linkedin.id)

        parser.contents = webpage_linkedin_contents2

        # call tested function
        parser.check_for_data()

        self.print_errors()

        entries = LinkDataController.objects.all()
        tags = LinkTagsDataModel.objects.all()

        self.assertEqual(entries.count(), 2)

        self.assertTrue(self.is_link("https://youtube.com"))
        self.assertTrue(self.is_link("https://tiktok.com"))

        self.assertEqual(tags.count(), 2)
