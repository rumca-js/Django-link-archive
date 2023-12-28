from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .utilities import WebPageDisabled
from ..pluginsources.sourceurlinterface import SourceUrlInterface



class SourceUrlInterfaceTest(WebPageDisabled, TestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_rss(self):
        url = SourceUrlInterface("https://www.codeproject.com/WebServices/NewsRSS.aspx")
        props = url.get_props()

        self.assertTrue(props)
        self.assertTrue("url" in props)
        self.assertTrue("title" in props)

    def test_youtube(self):
        url = SourceUrlInterface("https://www.youtube.com/watch?v=123")
        props = url.get_props()

        self.assertTrue(props)
        self.assertTrue("url" in props)
        self.assertTrue("title" in props)

    def test_html(self):
        url = SourceUrlInterface("https://linkedin.com")
        props = url.get_props()

        self.assertTrue(props)
        self.assertTrue("url" in props)
        self.assertTrue("title" in props)
