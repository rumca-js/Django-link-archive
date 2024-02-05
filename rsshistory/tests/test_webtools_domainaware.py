from datetime import datetime

from ..webtools import DomainAwarePage

from .fakeinternet import FakeInternetTestCase


class DomainAwarePageTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_is_mainstream_true(self):
        p = DomainAwarePage("http://www.youtube.com/test", "")
        self.assertTrue(p.is_mainstream())

        p = DomainAwarePage("http://youtube.com/?v=1234", "")
        self.assertTrue(p.is_mainstream())

        p = DomainAwarePage("http://youtu.be/djjdj", "")
        self.assertTrue(p.is_mainstream())

        p = DomainAwarePage("http://www.m.youtube.com/?v=1235", "")
        self.assertTrue(p.is_mainstream())

        p = DomainAwarePage("http://twitter.com/test", "")
        self.assertTrue(p.is_mainstream())

        p = DomainAwarePage("http://www.facebook.com/test", "")
        self.assertTrue(p.is_mainstream())

        p = DomainAwarePage("http://www.rumble.com/test", "")
        self.assertTrue(p.is_mainstream())

        p = DomainAwarePage("http://wikipedia.org/test", "")
        self.assertTrue(p.is_mainstream())

    def test_is_mainstream_false(self):
        # default language
        p = DomainAwarePage("http://test.com/my-site-test", "")
        self.assertTrue(not p.is_mainstream())

    def test_is_youtube_true(self):
        # default language
        p = DomainAwarePage("http://www.youtube.com/test", "")
        self.assertTrue(p.is_youtube())

        p = DomainAwarePage("http://youtube.com/?v=1234", "")
        self.assertTrue(p.is_youtube())

        p = DomainAwarePage("http://youtu.be/djjdj", "")
        self.assertTrue(p.is_youtube())

        p = DomainAwarePage("http://www.m.youtube.com/?v=1235", "")
        self.assertTrue(p.is_youtube())

        p = DomainAwarePage("http://twitter.com/test", "")
        self.assertFalse(p.is_youtube())

    def test_is_youtube_false(self):
        # default language
        p = DomainAwarePage("http://www.not-youtube.com/test", "")
        self.assertTrue(not p.is_youtube())

    def test_is_analytics_true(self):
        # default language
        p = DomainAwarePage("http://g.doubleclick.net/test", "")
        self.assertTrue(p.is_analytics())

    def test_is_analytics_false(self):
        # default language
        p = DomainAwarePage("http://test.com/my-site-test", "")
        self.assertTrue(not p.is_analytics())

    def test_is_link_service_true(self):
        # default language
        p = DomainAwarePage("http://lmg.gg/test", "")
        self.assertTrue(p.is_link_service())

    def test_is_link_service_false(self):
        # default language
        p = DomainAwarePage("http://lmg-not.gg/test", "")
        self.assertTrue(not p.is_link_service())
