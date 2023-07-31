from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from ..webtools import Page


webpage_no_lang = """<html>
</html>
"""

webpage_lang_not_default = """<html lang="it">
</html>
"""

webpage_no_title = """<html>
</html>
"""

webpage_title_lower = """<html>
 <title>This is a lower case title</title>
</html>
"""

webpage_title_upper = """<html>
 <TITLE>This is a upper case title</TITLE>
</html>
"""


class PageTest(TestCase):
    def test_get_domain(self):
        # default language
        p = Page("http://test.com/my-site-test", webpage_lang_not_default)
        self.assertEqual(p.get_domain(), "http://test.com")

    def test_get_domain_only(self):
        # default language
        p = Page("http://test.com/my-site-test", webpage_lang_not_default)
        self.assertEqual(p.get_domain_only(), "test.com")

    def test_default_language(self):
        # default language
        p = Page("http://test.com/my-site-test", webpage_no_lang)
        self.assertEqual(p.get_language(), "en")

    def test_language_it(self):
        # default language
        p = Page("http://test.com/my-site-test", webpage_lang_not_default)
        self.assertEqual(p.get_language(), "it")

    def test_no_title(self):
        # default language
        p = Page("http://test.com/my-site-test", webpage_no_title)
        self.assertEqual(p.get_title(), None)

    def test_title_lowercase(self):
        # default language
        p = Page("http://test.com/my-site-test", webpage_title_lower)
        self.assertEqual(p.get_title(), "This is a lower case title")

    def test_title_uppercase(self):
        # default language
        p = Page("http://test.com/my-site-test", webpage_title_upper)
        self.assertEqual(p.get_title(), "This is a upper case title")

    def test_is_youtube(self):
        # default language
        p = Page("http://youtube.com/?v=1234", webpage_title_upper)
        self.assertTrue(p.is_youtube())

        p = Page("http://youtu.be/djjdj", webpage_title_upper)
        self.assertTrue(p.is_youtube())

        p = Page("http://www.m.youtube/?v=1235", webpage_title_upper)
        self.assertTrue(p.is_youtube())

        p = Page("http://twitter.com/test", webpage_title_upper)
        self.assertFalse(p.is_youtube())

    def test_is_mainstream(self):
        # default language
        p = Page("http://youtube.com/?v=1234", webpage_title_upper)
        self.assertTrue(p.is_mainstream())

        p = Page("http://youtu.be/djjdj", webpage_title_upper)
        self.assertTrue(p.is_mainstream())

        p = Page("http://www.m.youtube/?v=1235", webpage_title_upper)
        self.assertTrue(p.is_mainstream())

        p = Page("http://twitter.com/test", webpage_title_upper)
        self.assertTrue(p.is_mainstream())

        p = Page("http://www.facebook.com/test", webpage_title_upper)
        self.assertTrue(p.is_mainstream())

        p = Page("http://www.rumble.com/test", webpage_title_upper)
        self.assertTrue(p.is_mainstream())

        p = Page("http://wikipedia.org/test", webpage_title_upper)
        self.assertTrue(p.is_mainstream())
