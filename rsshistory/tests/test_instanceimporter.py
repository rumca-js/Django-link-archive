import django.utils

from django.utils import timezone
from django.urls import reverse

from ..serializers.instanceimporter import InstanceImporter
from .fakeinternet import FakeInternetTestCase


class InstanceImporterTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_import_entries_no_page(self):
        importer = InstanceImporter("https://instance.com/entries", "renegat0x0")
        url = importer.get_next_page_link()
        self.assertEqual(url, "https://instance.com/entries?page=1")

    def test_import_entries_page_0(self):
        importer = InstanceImporter("https://instance.com/entries?page=0", "renegat0x0")
        url = importer.get_next_page_link()
        self.assertEqual(url, "https://instance.com/entries?page=1")

    def test_import_entries_args(self):
        importer = InstanceImporter(
            "https://instance.com/entries?v=1&page=0", "renegat0x0"
        )
        url = importer.get_next_page_link()
        self.assertEqual(url, "https://instance.com/entries?v=1&page=1")

    def test_import_entries(self):
        importer = InstanceImporter("https://instance.com/entries", "renegat0x0")

        # call tested function
        importer.import_all()

        self.assertTrue(True)

        # TODO check if tags were imported
        # TODO check if comments were imported

    def test_import_sources(self):
        importer = InstanceImporter("https://instance.com/sources", "renegat0x0")

        # call tested function
        importer.import_all()

        self.assertTrue(True)
