from datetime import datetime

from ..webtools import DomainAwarePage

from .fakeinternet import FakeInternetTestCase


class DomainAwarePageTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_is_mainstream_true(self):
        p = DomainAwarePage("http://www.youtube.com/test")
        self.assertTrue(p.is_mainstream())

        p = DomainAwarePage("http://youtube.com/?v=1234")
        self.assertTrue(p.is_mainstream())

        p = DomainAwarePage("http://youtu.be/djjdj")
        self.assertTrue(p.is_mainstream())

        p = DomainAwarePage("http://www.m.youtube.com/?v=1235")
        self.assertTrue(p.is_mainstream())

        p = DomainAwarePage("http://twitter.com/test")
        self.assertTrue(p.is_mainstream())

        p = DomainAwarePage("http://www.facebook.com/test")
        self.assertTrue(p.is_mainstream())

        p = DomainAwarePage("http://www.rumble.com/test")
        self.assertTrue(p.is_mainstream())

        p = DomainAwarePage("http://wikipedia.org/test")
        self.assertTrue(p.is_mainstream())

    def test_is_mainstream_false(self):
        # default language
        p = DomainAwarePage("http://test.com/my-site-test")
        self.assertTrue(not p.is_mainstream())

    def test_is_youtube_true(self):
        # default language
        p = DomainAwarePage("http://www.youtube.com/test")
        self.assertTrue(p.is_youtube())

        p = DomainAwarePage("http://youtube.com/?v=1234")
        self.assertTrue(p.is_youtube())

        p = DomainAwarePage("http://youtu.be/djjdj")
        self.assertTrue(p.is_youtube())

        p = DomainAwarePage("http://www.m.youtube.com/?v=1235")
        self.assertTrue(p.is_youtube())

        p = DomainAwarePage("http://twitter.com/test")
        self.assertFalse(p.is_youtube())

    def test_is_youtube_false(self):
        # default language
        p = DomainAwarePage("http://www.not-youtube.com/test")
        self.assertTrue(not p.is_youtube())

    def test_is_analytics_true(self):
        # default language
        p = DomainAwarePage("http://g.doubleclick.net/test")
        self.assertTrue(p.is_analytics())

    def test_is_analytics_false(self):
        # default language
        p = DomainAwarePage("http://test.com/my-site-test")
        self.assertTrue(not p.is_analytics())

    def test_is_link_service_true(self):
        # default language
        p = DomainAwarePage("http://lmg.gg/test")
        self.assertTrue(p.is_link_service())

    def test_is_link_service_false(self):
        # default language
        p = DomainAwarePage("http://lmg-not.gg/test")
        self.assertTrue(not p.is_link_service())

    def test_get_domain(self):
        # default language
        p = DomainAwarePage("http://test.com/my-site-test")
        self.assertEqual(p.get_domain(), "http://test.com")

    def test_get_domain_web_archive_link(self):
        link = "https://web.archive.org/web/20000229222350/http://www.quantumpicture.com/Flo_Control/flo_control.htm"
        p = DomainAwarePage(link)
        self.assertEqual(p.get_domain(), "https://web.archive.org")

    def test_get_domain_cell_link(self):
        link = "https://www.cell.com/cell/fulltext/S0092-8674(23)01344-2?_returnURL=https%3A%2F%2Flinkinghub.elsevier.com%2Fretrieve%2Fpii%2FS0092867423013442%3Fshowall%3Dtrue"
        p = DomainAwarePage(link)
        self.assertEqual(p.get_domain(), "https://www.cell.com")

    def test_is_domain_web_archive_link(self):
        link = "https://web.archive.org/web/20000229222350/http://www.quantumpicture.com/Flo_Control/flo_control.htm"
        p = DomainAwarePage(link)
        self.assertFalse(p.is_domain())

    def test_is_domain_cell_link(self):
        link = "https://www.cell.com/cell/fulltext/S0092-8674(23)01344-2?_returnURL=https%3A%2F%2Flinkinghub.elsevier.com%2Fretrieve%2Fpii%2FS0092867423013442%3Fshowall%3Dtrue"
        p = DomainAwarePage(link)
        self.assertFalse(p.is_domain())

    def test_get_domain_no_http(self):
        # default language
        p = DomainAwarePage("test.com")
        self.assertEqual(p.get_domain(), "https://test.com")

    def test_get_domain_only(self):
        # default language
        p = DomainAwarePage("http://test.com/my-site-test")
        self.assertEqual(p.get_domain_only(), "test.com")

    def test_get_page_ext_html(self):
        p = DomainAwarePage("http://mytestpage.com/page.html")
        ext = p.get_page_ext()

        self.assertTrue(ext == "html")

    def test_get_page_ext_htm(self):
        p = DomainAwarePage("http://mytestpage.com/page.htm")
        ext = p.get_page_ext()

        self.assertTrue(ext == "htm")

    def test_get_page_ext_js(self):
        p = DomainAwarePage("http://mytestpage.com/page.js")
        ext = p.get_page_ext()

        self.assertTrue(ext == "js")

    def test_get_page_ext_no_ext(self):
        p = DomainAwarePage("http://mytestpage.com")
        ext = p.get_page_ext()

        self.assertTrue(ext == None)

    def test_get_page_ext_html_args(self):
        p = DomainAwarePage("http://mytestpage.com/page.html?args=some")
        ext = p.get_page_ext()

        self.assertTrue(ext == "html")

    def test_get_url_full_normal_join_left_slash(self):
        url = DomainAwarePage.get_url_full(
            "http://mytestpage.com/test/", "images/facebook.com"
        )
        self.assertEqual(url, "http://mytestpage.com/test/images/facebook.com")

    def test_get_url_full_normal_join_right_slash(self):
        url = DomainAwarePage.get_url_full("http://mytestpage.com/test", "images/facebook.com")
        self.assertEqual(url, "http://mytestpage.com/test/images/facebook.com")

    def test_get_url_full_normal_join_no_slashes(self):
        url = DomainAwarePage.get_url_full("http://mytestpage.com/test", "images/facebook.com")
        self.assertEqual(url, "http://mytestpage.com/test/images/facebook.com")

    def test_get_url_full_normal_join_both_slashes(self):
        """
        slash in the link means that it is against the domain, not the current position.
        """
        url = DomainAwarePage.get_url_full(
            "http://mytestpage.com/test/", "/images/facebook.com"
        )
        self.assertEqual(url, "http://mytestpage.com/images/facebook.com")

    def test_get_url_full_path(self):
        url = DomainAwarePage.get_url_full(
            "http://mytestpage.com/test/", "/images/facebook.com"
        )
        self.assertEqual(url, "http://mytestpage.com/images/facebook.com")

    def test_get_url_full_double_path(self):
        url = DomainAwarePage.get_url_full(
            "http://mytestpage.com/test/", "//images/facebook.com"
        )
        self.assertEqual(url, "https://images/facebook.com")

    def test_get_url_full_http_path(self):
        url = DomainAwarePage.get_url_full(
            "http://mytestpage.com/test/", "http://images/facebook.com"
        )
        self.assertEqual(url, "http://images/facebook.com")

    def test_get_url_full_https_path(self):
        url = DomainAwarePage.get_url_full(
            "http://mytestpage.com/test/", "https://images/facebook.com"
        )
        self.assertEqual(url, "https://images/facebook.com")
