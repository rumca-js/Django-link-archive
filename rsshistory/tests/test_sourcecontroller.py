
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from ..controllers import SourceDataController


class SourceControllerTest(TestCase):
    def setUp(self):
        source_youtube = SourceDataController.objects.all().delete()

    def test_new_source(self):

        self.assertEqual(SourceDataController.objects.all().count(), 0)

        SourceDataController.add(
          {
            "url":"https://linkedin.com",
            "title":"LinkedIn",
            "category":"No",
            "subcategory":"No",
            "export_to_cms":False,
          }
        )

        self.assertEqual(SourceDataController.objects.all().count(), 1)

    def test_new_source_twice(self):

        self.assertEqual(SourceDataController.objects.all().count(), 0)

        SourceDataController.add(
          {
            "url":"https://linkedin.com",
            "title":"LinkedIn",
            "category":"No",
            "subcategory":"No",
            "export_to_cms":False,
          }
        )

        SourceDataController.add(
          {
            "url":"https://linkedin.com",
            "title":"LinkedIn",
            "category":"No",
            "subcategory":"No",
            "export_to_cms":False,
          }
        )

        self.assertEqual(SourceDataController.objects.all().count(), 1)
