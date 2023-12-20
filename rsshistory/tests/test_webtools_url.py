from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .utilities import WebPageDisabled
from ..webtools import Url


class UrlTest(WebPageDisabled, TestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_get_favicon(self):
        favicon = Url.get_favicon("https://multiple-favicons/page.html")

        self.assertEqual(
            favicon, "https://www.youtube.com/s/desktop/e4d15d2c/img/favicon.ico"
        )
