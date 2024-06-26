from ..webtools import Url, DomainCache, DomainCacheInfo

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class PageResponseObjectTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()


class DomainCacheInfoTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_cache_info__constructor(self):
        MockRequestCounter.mock_page_requests = 0

        # call tested function
        cache = DomainCache(cache_size = 400, use_robots_txt = True)
        cache_info = cache.get_domain_info("https://robots-txt.com/page.html")

        self.assertTrue(cache_info)

    def test_cache_info__url(self):
        MockRequestCounter.mock_page_requests = 0

        # call tested function
        cache = DomainCache(cache_size = 400, use_robots_txt = True)
        cache_info = cache.get_domain_info("https://robots-txt.com/page.html")

        self.assertEqual(cache_info.url, "https://robots-txt.com")

    def test_cache_info__robots_txt(self):
        MockRequestCounter.mock_page_requests = 0

        # call tested function
        cache = DomainCache(cache_size = 400, use_robots_txt = True)
        cache_info = cache.get_domain_info("https://robots-txt.com/page.html")

        self.assertEqual(cache_info.get_robots_txt_url(), "https://robots-txt.com/robots.txt")

    def test_cache_info__is_allowed(self):
        MockRequestCounter.mock_page_requests = 0

        # call tested function
        cache = DomainCache(cache_size = 400, use_robots_txt = True)
        cache_info = cache.get_domain_info("https://robots-txt.com/page.html")

        self.assertTrue(cache_info.is_allowed("https://robots-txt.com"))
        self.assertTrue(cache_info.is_allowed("https://robots-txt.com/robots.txt"))
        self.assertTrue(cache_info.is_allowed("https://robots-txt.com/anything"))
        self.assertFalse(cache_info.is_allowed("https://robots-txt.com/admin/"))
        self.assertFalse(cache_info.is_allowed("https://robots-txt.com/admin"))
