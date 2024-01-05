from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from ..controllers import (
    SourceDataController,
    BackgroundJobController,
)
from .utilities import WebPageDisabled


class SourceControllerTest(WebPageDisabled, TestCase):
    def setUp(self):
        source_youtube = SourceDataController.objects.all().delete()
        self.disable_web_pages()

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

        # adding a source adds request to fetch data from it
        self.assertEqual(BackgroundJobController.objects.all().count(), 1)

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

    def test_source_favicon(self):
        source = SourceDataController.add(
            {
                "url": "https://linkedin.com",
                "title": "LinkedIn",
                "category": "No",
                "subcategory": "No",
                "export_to_cms": False,
            }
        )

        self.assertTrue(source.get_favicon() == "https://linkedin.com/favicon.ico")

    def test_source_get_full_information_page(self):
        url = "https://linkedin.com"

        SourceDataController.objects.all().delete()

        props = SourceDataController.get_full_information({"url": url})

        self.assertTrue(props != None)
        self.assertTrue(len(props) > 0)

    def test_source_get_full_information_youtube(self):
        url = "https://www.youtube.com/watch?v=12312312"

        SourceDataController.objects.all().delete()

        props = SourceDataController.get_full_information({"url": url})

        self.assertTrue(props != None)
        self.assertTrue(len(props) > 0)
