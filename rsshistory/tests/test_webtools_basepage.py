from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from ..webtools import BasePage


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

webpage_title_meta_og = """<html>
 <TITLE>selected meta title</TITLE>
 <meta property="og:title" content="selected og:title" />
</html>
"""

webpage_description_meta_og = """<html>
 <description>selected meta description</TITLE>
 <meta property="og:description" content="selected og:description" />
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
 <a custom-peroperty="custom-property-value" href="//test6.domain.com/" class="class">
   <picture></picture>
   </a>
</html>
"""


class BasePageTest(TestCase):
    def test_get_domain(self):
        # default language
        p = BasePage("http://test.com/my-site-test", webpage_lang_not_default)
        self.assertEqual(p.get_domain(), "http://test.com")

    def test_get_domain_only(self):
        # default language
        p = BasePage("http://test.com/my-site-test", webpage_lang_not_default)
        self.assertEqual(p.get_domain_only(), "test.com")

    def test_get_page_ext_html(self):
        p = BasePage("http://mytestpage.com/page.html", webpage_links)
        ext = p.get_page_ext()

        self.assertTrue(ext == "html")

    def test_get_page_ext_htm(self):
        p = BasePage("http://mytestpage.com/page.htm", webpage_links)
        ext = p.get_page_ext()

        self.assertTrue(ext == "htm")

    def test_get_page_ext_js(self):
        p = BasePage("http://mytestpage.com/page.js", webpage_links)
        ext = p.get_page_ext()

        self.assertTrue(ext == "js")

    def test_get_page_ext_no_ext(self):
        p = BasePage("http://mytestpage.com", webpage_links)
        ext = p.get_page_ext()

        self.assertTrue(ext == "")

    def test_get_page_ext_html_args(self):
        p = BasePage("http://mytestpage.com/page.html?args=some", webpage_links)
        ext = p.get_page_ext()

        self.assertTrue(ext == "html")
