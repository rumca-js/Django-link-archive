import hashlib
from ..webtools import BasePage, InputContent, PageOptions, calculate_hash

from .fakeinternet import FakeInternetTestCase


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


class PageOptionsTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_use_selenium_full(self):
        o = PageOptions()
        o.use_selenium_full = True

        # call tested function
        self.assertTrue(o.is_selenium())

    def test_use_selenium_headless(self):
        o = PageOptions()
        o.use_selenium_headless = True

        # call tested function
        self.assertTrue(o.is_selenium())

    def test_use_selenium_both(self):
        o = PageOptions()
        o.use_selenium_headless = True
        o.use_selenium_full = True

        # call tested function
        self.assertTrue(o.is_selenium())

    def test_not_use_selenium_full(self):
        o = PageOptions()
        o.use_selenium_full = True

        # call tested function
        self.assertFalse(o.is_not_selenium())

    def test_not_use_selenium_headless(self):
        o = PageOptions()
        o.use_selenium_headless = True

        # call tested function
        self.assertFalse(o.is_not_selenium())

    def test_not_use_selenium_both(self):
        o = PageOptions()
        o.use_selenium_headless = True
        o.use_selenium_full = True

        # call tested function
        self.assertFalse(o.is_not_selenium())

    def test_not_use_selenium_none(self):
        o = PageOptions()
        o.use_selenium_headless = False
        o.use_selenium_full = False

        # call tested function
        self.assertTrue(o.is_not_selenium())


class BasePageTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_calculate_hash(self):
        self.assertEqual(
            BasePage.calculate_hash(webpage_links),
            hashlib.md5(text.encode("utf-8")).digest(),
        )

    def test_calculate_hash(self):
        self.assertEqual(
            calculate_hash(webpage_links),
            hashlib.md5(webpage_links.encode("utf-8")).digest(),
        )


class InputContentTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_htmlify_two_normal_links(self):
        content = """this is <a href="https://first-link.com">First Link</a>
        this is <a href="https://second-link.com">Second Link</a>"""

        c = InputContent(content)
        result = c.htmlify()
        self.assertEqual(result, content)

    def test_htmlify_pure_links(self):
        content = """this is https://first-link.com
        this is https://second-link.com"""

        c = InputContent(content)
        result = c.htmlify()

        expected_result = """this is <a href="https://first-link.com">https://first-link.com</a>
        this is <a href="https://second-link.com">https://second-link.com</a>"""

        self.assertEqual(result, expected_result)

    def test_htmlify_removes_attrs(self):
        content = """this is <a href="https://first-link.com" style="clear:both">First Link</a>
        this is <a href="https://second-link.com" style="display:flex">Second Link</a>"""

        c = InputContent(content)
        result = c.htmlify()

        expected_result = """this is <a href="https://first-link.com">First Link</a>
        this is <a href="https://second-link.com">Second Link</a>"""

        self.assertEqual(result, expected_result)
