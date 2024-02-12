import hashlib
from ..webtools import BasePage, InputContent, PageOptions

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

    def test_get_domain(self):
        # default language
        p = BasePage("http://test.com/my-site-test", webpage_lang_not_default)
        self.assertEqual(p.get_domain(), "http://test.com")

    def test_get_domain_web_archive_link(self):
        link = "https://web.archive.org/web/20000229222350/http://www.quantumpicture.com/Flo_Control/flo_control.htm"
        p = BasePage(link, "")
        self.assertEqual(p.get_domain(), "https://web.archive.org")

    def test_get_domain_cell_link(self):
        link = "https://www.cell.com/cell/fulltext/S0092-8674(23)01344-2?_returnURL=https%3A%2F%2Flinkinghub.elsevier.com%2Fretrieve%2Fpii%2FS0092867423013442%3Fshowall%3Dtrue"
        p = BasePage(link, "")
        self.assertEqual(p.get_domain(), "https://www.cell.com")

    def test_is_domain_web_archive_link(self):
        link = "https://web.archive.org/web/20000229222350/http://www.quantumpicture.com/Flo_Control/flo_control.htm"
        p = BasePage(link, "")
        self.assertFalse(p.is_domain())

    def test_is_domain_cell_link(self):
        link = "https://www.cell.com/cell/fulltext/S0092-8674(23)01344-2?_returnURL=https%3A%2F%2Flinkinghub.elsevier.com%2Fretrieve%2Fpii%2FS0092867423013442%3Fshowall%3Dtrue"
        p = BasePage(link, "")
        self.assertFalse(p.is_domain())

    def test_get_domain_no_http(self):
        # default language
        p = BasePage("test.com", webpage_lang_not_default)
        self.assertEqual(p.get_domain(), "https://test.com")

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

        self.assertTrue(ext == None)

    def test_get_page_ext_html_args(self):
        p = BasePage("http://mytestpage.com/page.html?args=some", webpage_links)
        ext = p.get_page_ext()

        self.assertTrue(ext == "html")

    def test_get_url_full_normal_join_left_slash(self):
        url = BasePage.get_url_full(
            "http://mytestpage.com/test/", "images/facebook.com"
        )
        self.assertEqual(url, "http://mytestpage.com/test/images/facebook.com")

    def test_get_url_full_normal_join_right_slash(self):
        url = BasePage.get_url_full("http://mytestpage.com/test", "images/facebook.com")
        self.assertEqual(url, "http://mytestpage.com/test/images/facebook.com")

    def test_get_url_full_normal_join_no_slashes(self):
        url = BasePage.get_url_full("http://mytestpage.com/test", "images/facebook.com")
        self.assertEqual(url, "http://mytestpage.com/test/images/facebook.com")

    def test_get_url_full_normal_join_both_slashes(self):
        """
        slash in the link means that it is against the domain, not the current position.
        """
        url = BasePage.get_url_full(
            "http://mytestpage.com/test/", "/images/facebook.com"
        )
        self.assertEqual(url, "http://mytestpage.com/images/facebook.com")

    def test_get_url_full_path(self):
        url = BasePage.get_url_full(
            "http://mytestpage.com/test/", "/images/facebook.com"
        )
        self.assertEqual(url, "http://mytestpage.com/images/facebook.com")

    def test_get_url_full_double_path(self):
        url = BasePage.get_url_full(
            "http://mytestpage.com/test/", "//images/facebook.com"
        )
        self.assertEqual(url, "https://images/facebook.com")

    def test_get_url_full_http_path(self):
        url = BasePage.get_url_full(
            "http://mytestpage.com/test/", "http://images/facebook.com"
        )
        self.assertEqual(url, "http://images/facebook.com")

    def test_get_url_full_https_path(self):
        url = BasePage.get_url_full(
            "http://mytestpage.com/test/", "https://images/facebook.com"
        )
        self.assertEqual(url, "https://images/facebook.com")

    def test_calculate_hash(self):
        p = BasePage("http://mytestpage.com/test/", webpage_links)
        self.assertEqual(p.calculate_hash(), hashlib.md5(text.encode("utf-8")).digest())

    def test_calculate_hash(self):
        p = BasePage("http://mytestpage.com/test/", webpage_links)
        self.assertEqual(p.calculate_hash(webpage_links), hashlib.md5(webpage_links.encode("utf-8")).digest())

    def test_get_content_hash(self):
        p = BasePage("http://mytestpage.com/test/", webpage_links)
        self.assertEqual(p.get_contents_hash(), hashlib.md5(webpage_links.encode("utf-8")).digest())


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
