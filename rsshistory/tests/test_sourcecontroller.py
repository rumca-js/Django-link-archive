from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from ..controllers import SourceDataController


class RequestsObject(object):
    def __init__(self, url, headers, timeout):
        self.status_code = 200
        self.apparent_encoding = "utf-8"
        self.encoding = "utf-8"
        self.text = "text"
        self.content = "text"


class SourceControllerTest(TestCase):
    def setUp(self):
        source_youtube = SourceDataController.objects.all().delete()
        self.disable_web_pages()

    def get_contents_function(self, url, headers, timeout):
        print("Mocked Requesting page: {}".format(url))
        return RequestsObject(url, headers, timeout)

    def disable_web_pages(self):
        from ..webtools import BasePage, HtmlPage

        BasePage.get_contents_function = self.get_contents_function
        HtmlPage.get_contents_function = self.get_contents_function

    def test_new_source(self):
        self.assertEqual(SourceDataController.objects.all().count(), 0)

        SourceDataController.add(
            {
                "url": "https://linkedin.com",
                "title": "LinkedIn",
                "category": "No",
                "subcategory": "No",
                "export_to_cms": False,
            }
        )

        self.assertEqual(SourceDataController.objects.all().count(), 1)

    def test_new_source_twice(self):
        self.assertEqual(SourceDataController.objects.all().count(), 0)

        SourceDataController.add(
            {
                "url": "https://linkedin.com",
                "title": "LinkedIn",
                "category": "No",
                "subcategory": "No",
                "export_to_cms": False,
            }
        )

        SourceDataController.add(
            {
                "url": "https://linkedin.com",
                "title": "LinkedIn",
                "category": "No",
                "subcategory": "No",
                "export_to_cms": False,
            }
        )

        self.assertEqual(SourceDataController.objects.all().count(), 1)
