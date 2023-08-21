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

webpage_links = """<html>
 <TITLE>This is a upper case title</TITLE>
 <a custom-peroperty="custom-property-value" href="http://otherpage1.net" class="class">
   <picture></picture>
   </a>
 <a custom-peroperty="custom-property-value" href="https://otherpage2.net" class="class">
   <picture></picture>
   </a>
 <a custom-peroperty="custom-property-value" href="/test/test1" class="contentLink  hero--img -first">
   <picture></picture>
   </a>
 <a custom-peroperty="custom-property-value" href="/test/test2.html" class="class">
   <picture></picture>
   </a>
 <a custom-peroperty="custom-property-value" href="/test/test3.htm" class="class">
   <picture></picture>
   </a>
 <a custom-peroperty="custom-property-value" href="/test/test4.js" class="class">
   <picture></picture>
   </a>
 <a custom-peroperty="custom-property-value" href="/test/test5/" class="class">
   <picture></picture>
   </a>
 <a custom-peroperty="custom-property-value" href="//test6/" class="class">
   <picture></picture>
   </a>
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

    def test_get_links(self):
        p = Page("http://mytestpage.com/?argument=value", webpage_links)

        links = p.get_links()

        self.assertTrue("http://otherpage1.net" in links)
        self.assertTrue("https://otherpage2.net" in links)

        self.assertTrue("http://mytestpage.com/test/test1" in links)
        self.assertTrue("http://mytestpage.com/test/test2.html" in links)
        self.assertTrue("http://mytestpage.com/test/test3.htm" in links)
        self.assertTrue("http://mytestpage.com/test/test4.js" in links)
        self.assertTrue("http://mytestpage.com/test/test5/" in links)
        self.assertTrue("http://mytestpage.com/test6/" in links)
