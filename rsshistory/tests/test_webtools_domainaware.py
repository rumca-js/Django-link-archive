from datetime import datetime

from ..webtools import DomainAwarePage

from .fakeinternet import FakeInternetTestCase


class DomainAwarePageTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_is_mainstream_true(self):
        p = DomainAwarePage("http://www.youtube.com/test")
        # call tested function
        self.assertTrue(p.is_mainstream())

        p = DomainAwarePage("http://youtube.com/?v=1234")
        # call tested function
        self.assertTrue(p.is_mainstream())

        p = DomainAwarePage("http://youtu.be/djjdj")
        # call tested function
        self.assertTrue(p.is_mainstream())

        p = DomainAwarePage("http://www.m.youtube.com/?v=1235")
        # call tested function
        self.assertTrue(p.is_mainstream())

        p = DomainAwarePage("http://twitter.com/test")
        # call tested function
        self.assertTrue(p.is_mainstream())

        p = DomainAwarePage("http://www.facebook.com/test")
        # call tested function
        self.assertTrue(p.is_mainstream())

        p = DomainAwarePage("http://www.rumble.com/test")
        # call tested function
        self.assertTrue(p.is_mainstream())

        p = DomainAwarePage("http://wikipedia.org/test")
        # call tested function
        self.assertTrue(p.is_mainstream())

    def test_is_mainstream_false(self):
        p = DomainAwarePage("http://test.com/my-site-test")
        # call tested function
        self.assertTrue(not p.is_mainstream())

    def test_is_youtube_true(self):
        p = DomainAwarePage("http://www.youtube.com/test")
        # call tested function
        self.assertTrue(p.is_youtube())

        p = DomainAwarePage("http://youtube.com/?v=1234")
        # call tested function
        self.assertTrue(p.is_youtube())

        p = DomainAwarePage("http://youtu.be/djjdj")
        # call tested function
        self.assertTrue(p.is_youtube())

        p = DomainAwarePage("http://www.m.youtube.com/?v=1235")
        # call tested function
        self.assertTrue(p.is_youtube())

        p = DomainAwarePage("http://twitter.com/test")
        # call tested function
        self.assertFalse(p.is_youtube())

    def test_is_youtube_false(self):
        p = DomainAwarePage("http://www.not-youtube.com/test")
        # call tested function
        self.assertTrue(not p.is_youtube())

    def test_is_analytics_true(self):
        p = DomainAwarePage("http://g.doubleclick.net/test")
        # call tested function
        self.assertTrue(p.is_analytics())

    def test_is_analytics_false(self):
        p = DomainAwarePage("http://test.com/my-site-test")
        # call tested function
        self.assertTrue(not p.is_analytics())

    def test_is_link_service_true(self):
        p = DomainAwarePage("http://lmg.gg/test")
        # call tested function
        self.assertTrue(p.is_link_service())

    def test_is_link_service_false(self):
        p = DomainAwarePage("http://lmg-not.gg/test")
        # call tested function
        self.assertTrue(not p.is_link_service())

    def test_get_domain_http(self):
        p = DomainAwarePage("http://test.com/my-site-test")
        # call tested function
        self.assertEqual(p.get_domain(), "http://test.com")

    def test_get_domain_http_digits(self):
        p = DomainAwarePage("http://127.0.0.1/my-site-test")
        # call tested function
        self.assertEqual(p.get_domain(), "http://127.0.0.1")

    def test_get_domain_ftp(self):
        p = DomainAwarePage("ftp://test.com/my-site-test")
        # call tested function
        self.assertEqual(p.get_domain(), "ftp://test.com")

    def test_get_domain_smb(self):
        p = DomainAwarePage("smb://test.com/my-site-test")
        # call tested function
        self.assertEqual(p.get_domain(), "smb://test.com")

    def test_get_domain_smb_lin(self):
        p = DomainAwarePage("//test.com/my-site-test")
        # call tested function
        self.assertEqual(p.get_domain(), "//test.com")

    def test_get_domain_smb_win(self):
        p = DomainAwarePage("\\\\test.com\\my-site-test")
        # call tested function
        self.assertEqual(p.get_domain(), "\\\\test.com")

    def test_get_domain__null(self):
        p = DomainAwarePage(None)
        # call tested function
        self.assertEqual(p.get_domain(), None)

    def test_get_domain__email(self):
        p = DomainAwarePage("https://user@gmail.com")
        # call tested function
        self.assertEqual(p.get_domain(), "https://gmail.com")

    def test_get_domain_web_archive_link(self):
        link = "https://web.archive.org/web/20000229222350/http://www.quantumpicture.com/Flo_Control/flo_control.htm"
        p = DomainAwarePage(link)
        # call tested function
        self.assertEqual(p.get_domain(), "https://web.archive.org")

    def test_get_domain_cell_link(self):
        link = "https://www.cell.com/cell/fulltext/S0092-8674(23)01344-2?_returnURL=https%3A%2F%2Flinkinghub.elsevier.com%2Fretrieve%2Fpii%2FS0092867423013442%3Fshowall%3Dtrue"
        p = DomainAwarePage(link)
        # call tested function
        self.assertEqual(p.get_domain(), "https://www.cell.com")

    def test_is_domain_web_archive_link(self):
        link = "https://web.archive.org/web/20000229222350/http://www.quantumpicture.com/Flo_Control/flo_control.htm"
        p = DomainAwarePage(link)
        # call tested function
        self.assertFalse(p.is_domain())

    def test_is_domain_cell_link(self):
        link = "https://www.cell.com/cell/fulltext/S0092-8674(23)01344-2?_returnURL=https%3A%2F%2Flinkinghub.elsevier.com%2Fretrieve%2Fpii%2FS0092867423013442%3Fshowall%3Dtrue"
        p = DomainAwarePage(link)
        # call tested function
        self.assertFalse(p.is_domain())

    def test_get_domain_no_http(self):
        p = DomainAwarePage("test.com")
        # call tested function
        self.assertEqual(p.get_domain(), "https://test.com")

    def test_get_domain_https_uppercase(self):
        p = DomainAwarePage("HTTPS://test.com")
        # call tested function
        self.assertEqual(p.get_domain(), "https://test.com")

    def test_get_domain_port(self):
        p = DomainAwarePage("https://my-server:8185/view/somethingsomething")
        # call tested function
        self.assertEqual(p.get_domain(), "https://my-server")

    def test_get_domain_odysee(self):
        p = DomainAwarePage("https://odysee.com/@MetalRockRules!:1/Metallica---The-Memory-Remains--Music-Video-HD-Remastered-:6")
        # call tested function
        self.assertEqual(p.get_domain(), "https://odysee.com")

    def test_get_domain_only(self):
        p = DomainAwarePage("http://test.com/my-site-test")
        # call tested function
        self.assertEqual(p.get_domain_only(), "test.com")

    def test_get_page_ext_html(self):
        p = DomainAwarePage("http://mytestpage.com/page.html")
        # call tested function
        ext = p.get_page_ext()

        self.assertTrue(ext == "html")

    def test_get_page_ext_htm(self):
        p = DomainAwarePage("http://mytestpage.com/page.htm")
        # call tested function
        ext = p.get_page_ext()

        self.assertTrue(ext == "htm")

    def test_get_page_ext_js(self):
        p = DomainAwarePage("http://mytestpage.com/page.js")
        # call tested function
        ext = p.get_page_ext()

        self.assertTrue(ext == "js")

    def test_get_page_ext_no_ext(self):
        p = DomainAwarePage("http://mytestpage.com")
        # call tested function
        ext = p.get_page_ext()

        self.assertTrue(ext == None)

    def test_get_page_ext_html_args(self):
        p = DomainAwarePage("http://mytestpage.com/page.html?args=some")
        # call tested function
        ext = p.get_page_ext()

        self.assertTrue(ext == "html")

    def test_get_url_full_normal_join_left_slash(self):
        # call tested function
        url = DomainAwarePage.get_url_full(
            "http://mytestpage.com/test/", "images/facebook.com"
        )
        self.assertEqual(url, "http://mytestpage.com/test/images/facebook.com")

    def test_get_url_full_normal_join_right_slash(self):
        # call tested function
        url = DomainAwarePage.get_url_full(
            "http://mytestpage.com/test", "images/facebook.com"
        )
        self.assertEqual(url, "http://mytestpage.com/test/images/facebook.com")

    def test_get_url_full_normal_join_no_slashes(self):
        # call tested function
        url = DomainAwarePage.get_url_full(
            "http://mytestpage.com/test", "images/facebook.com"
        )
        self.assertEqual(url, "http://mytestpage.com/test/images/facebook.com")

    def test_get_url_full_normal_join_both_slashes(self):
        """
        slash in the link means that it is against the domain, not the current position.
        """
        # call tested function
        url = DomainAwarePage.get_url_full(
            "http://mytestpage.com/test/", "/images/facebook.com"
        )
        self.assertEqual(url, "http://mytestpage.com/images/facebook.com")

    def test_get_url_full_path(self):
        # call tested function
        url = DomainAwarePage.get_url_full(
            "http://mytestpage.com/test/", "/images/facebook.com"
        )
        self.assertEqual(url, "http://mytestpage.com/images/facebook.com")

    def test_get_url_full_double_path(self):
        # call tested function
        url = DomainAwarePage.get_url_full(
            "http://mytestpage.com/test/", "//images/facebook.com"
        )
        self.assertEqual(url, "https://images/facebook.com")

    def test_get_url_full_http_path(self):
        # call tested function
        url = DomainAwarePage.get_url_full(
            "http://mytestpage.com/test/", "http://images/facebook.com"
        )
        self.assertEqual(url, "http://images/facebook.com")

    def test_get_url_full_https_path(self):
        # call tested function
        url = DomainAwarePage.get_url_full(
            "http://mytestpage.com/test/", "https://images/facebook.com"
        )
        self.assertEqual(url, "https://images/facebook.com")

    def test_up(self):
        p = DomainAwarePage("http://www.youtube.com/test1/test2")

        # call tested function
        p = p.up()

        self.assertTrue(p)
        self.assertEqual(p.url, "http://www.youtube.com/test1")

        # call tested function
        p = p.up()

        self.assertTrue(p)
        self.assertEqual(p.url, "http://www.youtube.com")

        # call tested function
        p = p.up()

        self.assertTrue(p)
        self.assertEqual(p.url, "http://youtube.com")

        # call tested function
        p = p.up()

        self.assertFalse(p)

    def test_split(self):
        p = DomainAwarePage("http://www.youtube.com/test1/test2?whatever=1&something=2")
        # call tested function
        parts = p.split()

        print(parts)

        self.assertEqual(len(parts), 6)

        self.assertEqual(parts[0], "http")
        self.assertEqual(parts[1], "://")
        self.assertEqual(parts[2], "www.youtube.com")
        self.assertEqual(parts[3], "test1")
        self.assertEqual(parts[4], "test2")
        self.assertEqual(parts[5], "?whatever=1&something=2")

    def test_join(self):
        parts = [
            "http",
            "://",
            "www.youtube.com",
            "test1",
            "test2",
            "?whatever=1&something=2",
        ]

        p = DomainAwarePage("")
        # call tested function
        result = p.join(parts)

        self.assertEqual(
            result, "http://www.youtube.com/test1/test2?whatever=1&something=2"
        )

    def test_parse_url(self):
        p = DomainAwarePage("https://www.youtube.com/test?parameter=True")
        parts = p.parse_url()
        print(parts)

        self.assertEqual(len(parts), 5)
        self.assertEqual(parts[0], "https")
        self.assertEqual(parts[1], "://")
        self.assertEqual(parts[2], "www.youtube.com")
        self.assertEqual(parts[3], "/test")
        self.assertEqual(parts[4], "?parameter=True")

    def test_parse_url2(self):
        p = DomainAwarePage("https://www.youtube.com/test#parameter=True")
        parts = p.parse_url()
        print(parts)

        self.assertEqual(len(parts), 5)
        self.assertEqual(parts[0], "https")
        self.assertEqual(parts[1], "://")
        self.assertEqual(parts[2], "www.youtube.com")
        self.assertEqual(parts[3], "/test")
        self.assertEqual(parts[4], "#parameter=True")

    def test_parse_url3(self):
        p = DomainAwarePage("https://www.youtube.com/test/")
        parts = p.parse_url()
        print(parts)

        self.assertEqual(len(parts), 4)
        self.assertEqual(parts[0], "https")
        self.assertEqual(parts[1], "://")
        self.assertEqual(parts[2], "www.youtube.com")
        self.assertEqual(parts[3], "/test/")

    def test_parse_url__port(self):
        p = DomainAwarePage("https://www.youtube.com:443/test?parameter=True")
        parts = p.parse_url()
        print(parts)

        self.assertEqual(len(parts), 5)
        self.assertEqual(parts[0], "https")
        self.assertEqual(parts[1], "://")
        self.assertEqual(parts[2], "www.youtube.com:443")
        self.assertEqual(parts[3], "/test")
        self.assertEqual(parts[4], "?parameter=True")

    def test_is_web_link(self):
        p = DomainAwarePage("https://www.youtube.com")
        # call tested function
        self.assertTrue(p.is_web_link())

        p = DomainAwarePage("https://youtube.com")
        # call tested function
        self.assertTrue(p.is_web_link())

        p = DomainAwarePage("https://com")
        # call tested function
        self.assertFalse(p.is_web_link())

        p = DomainAwarePage("smb://youtube.com")
        # call tested function
        self.assertTrue(p.is_web_link())

        p = DomainAwarePage("ftp://youtube.com")
        # call tested function
        self.assertTrue(p.is_web_link())

        p = DomainAwarePage("//127.0.0.1")
        # call tested function
        self.assertTrue(p.is_web_link())

        p = DomainAwarePage("\\\\127.0.0.1")
        # call tested function
        self.assertTrue(p.is_web_link())

    def test_get_protocolless(self):
        p = DomainAwarePage("https://www.youtube.com:443")
        # call tested function
        self.assertEqual(p.get_protocolless(), "www.youtube.com:443")

        p = DomainAwarePage("https://www.youtube.com:443/test")
        # call tested function
        self.assertEqual(p.get_protocolless(), "www.youtube.com:443/test")

    def test_get_port__full_url(self):
        p = DomainAwarePage("https://www.youtube.com:443/test?parameter=True")
        port = p.get_port()

        self.assertEqual(port, 443)

    def test_get_port__domain_only(self):
        p = DomainAwarePage("https://www.youtube.com:443")
        port = p.get_port()

        self.assertEqual(port, 443)
