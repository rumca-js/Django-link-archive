from django.contrib.auth.models import User

from ..models import UserTags, SourceOperationalData
from ..controllers import SourceDataController, LinkDataController, BackgroundJobController

from ..pluginsources import BaseParsePlugin
from ..pluginsources import SourceParseInternalLinks
from ..pluginsources import DomainParserPlugin
from ..pluginsources import NowNowNowParserPlugin
from ..pluginsources import RssParserPlugin
from ..pluginsources import HackerNewsParserPlugin

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

        self.user = User.objects.create_user(
            username="test_username", password="testpassword", is_superuser=True
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
        self.assertTrue(parse.is_link_valid("https://github.com/location/inside"))

    def test_is_link_valid_js(self):
        parse = BaseParsePlugin(self.source_youtube.id)
        self.assertFalse(parse.is_link_valid("https://youtube.com/location/inside.js"))

    def test_is_link_valid_css(self):
        parse = BaseParsePlugin(self.source_youtube.id)
        self.assertFalse(parse.is_link_valid("https://youtube.com/location/inside.css"))


class SourceParseInternalLinksPluginTest(FakeInternetTestCase):
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
        parse = SourceParseInternalLinks(self.source_youtube.id)
        self.assertTrue(parse.is_link_valid("https://youtube.com/location/inside.html"))

    def test_is_link_valid_htm(self):
        parse = SourceParseInternalLinks(self.source_youtube.id)
        self.assertTrue(parse.is_link_valid("https://youtube.com/location/inside.htm"))

    def test_is_link_valid_ending_dash(self):
        parse = SourceParseInternalLinks(self.source_youtube.id)
        self.assertTrue(parse.is_link_valid("https://youtube.com/location/inside/"))

    def test_is_link_valid_ending_noext(self):
        parse = SourceParseInternalLinks(self.source_youtube.id)
        self.assertTrue(parse.is_link_valid("https://youtube.com/location/inside"))

    # check if false

    def test_is_link_valid_outside_location(self):
        parse = SourceParseInternalLinks(self.source_youtube.id)
        self.assertFalse(parse.is_link_valid("https://github.com/location/inside"))

    def test_is_link_valid_js(self):
        parse = SourceParseInternalLinks(self.source_youtube.id)
        self.assertFalse(parse.is_link_valid("https://youtube.com/location/inside.js"))

    def test_is_link_valid_css(self):
        parse = SourceParseInternalLinks(self.source_youtube.id)
        self.assertFalse(parse.is_link_valid("https://youtube.com/location/inside.css"))


class DomainParsePluginTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.source_youtube = SourceDataController.objects.create(
            url="https://page-with-two-links.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )

        self.setup_configuration()

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

        self.assertEqual(len(props), 0)

        jobs = BackgroundJobController.objects.all().values_list("subject", flat=True)
        self.assertEqual(len(jobs), 2)

        self.assertTrue("https://link1.com" in jobs)
        self.assertTrue("https://link2.com" in jobs)

        #TODO check if jobs have source in cfg?


class RssParserPluginTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.source_youtube = SourceDataController.objects.create(
            url="https://hnrss.org/frontpage",
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
        parser = RssParserPlugin(self.source_youtube.id)

        # call tested function
        props = list(parser.get_container_elements())

        self.assertEqual(len(props), 20)

        jobs = BackgroundJobController.objects.all().values_list("subject", flat=True)

        self.assertTrue(jobs.count() > 0)


class HackerNewsParserPluginTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.source_youtube = SourceDataController.objects.create(
            url="https://hnrss.org/frontpage",
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
        parser = HackerNewsParserPlugin(self.source_youtube.id)

        # call tested function
        props = list(parser.get_container_elements())

        self.assertEqual(len(props), 20)

        self.assertEqual(props[0]["source"], "https://hnrss.org/frontpage")


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
            url="https://page-with-two-links.com",
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

        # call tested function
        props = list(parser.get_container_elements())

        self.assertEqual(len(props), 0)

        jobs = BackgroundJobController.objects.all().values_list("subject", flat=True)

        self.assertEqual(jobs.count(), 2)

        self.assertTrue("https://link1.com" in jobs)
        self.assertTrue("https://link2.com" in jobs)

        # TODO check if source is in jobs cfg


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
            url="https://page-with-two-links.com",
            title="linkedin",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )

        self.user = User.objects.create_user(
            username="test_username", password="testpassword", is_superuser=True
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

        # call tested function
        props = list(parser.get_container_elements())

        self.print_errors()

        self.assertEqual(len(props), 0)

        jobs = BackgroundJobController.objects.all().values_list("subject", flat=True)
        self.assertEqual(len(jobs), 2)

        self.assertTrue("https://link1.com" in jobs)
        self.assertTrue("https://link2.com" in jobs)

        # TODO check if source is in job cfg

    def test_check_for_data(self):
        LinkDataController.objects.all().delete()
        UserTags.objects.all().delete()
        SourceOperationalData.objects.all().delete()

        parser = NowNowNowParserPlugin(self.source_linkedin.id)

        # call tested function
        parser.check_for_data()

        self.print_errors()

        self.assertTrue(parser.hash)

        entries = LinkDataController.objects.all()
        tags = UserTags.objects.all()

        self.assertEqual(entries.count(), 0)

        jobs = BackgroundJobController.objects.all().values_list("subject", flat=True)
        self.assertEqual(len(jobs), 2)

        self.assertTrue("https://link1.com" in jobs)
        self.assertTrue("https://link2.com" in jobs)

        # TODO should check if tags and user is in cfg
