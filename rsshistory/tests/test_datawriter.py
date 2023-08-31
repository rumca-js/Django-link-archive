from pathlib import Path
import shutil
from datetime import datetime

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from ..models import ConfigurationEntry, PersistentInfo, Domains
from ..controllers import SourceDataController, LinkDataController
from ..configuration import Configuration
from ..datawriter import DataWriter


class DataWriterTest(TestCase):
    def setUp(self):
        self.test_export_path = Path("./test_data/exports")
        self.remove_all_files()

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )
        LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=bookmarked",
            title="The first link",
            source_obj=source_youtube,
            bookmarked=True,
            date_published=datetime.strptime("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=nonbookmarked",
            title="The second link",
            source_obj=source_youtube,
            bookmarked=False,
            date_published=datetime.strptime("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        SourceDataController.objects.create(
            url="https://linkedin.com",
            title="LinkedIn",
            category="No",
            subcategory="No",
            export_to_cms=False,
        )

        Domains.add("https://youtube.com?v=nonbookmarked")

    def tearDown(self):
        self.remove_all_files()

    def remove_all_files(self):
        if self.test_export_path.exists():
            shutil.rmtree(self.test_export_path.as_posix())
            shutil.rmtree(self.test_export_path.parent.as_posix())

    def test_write_bookmarks(self):
        import json

        entry = ConfigurationEntry.get()
        entry.data_export_path = self.test_export_path
        entry.save()

        conf = Configuration.get_object()

        writer = DataWriter(conf)
        writer.write_bookmarks()

        links = LinkDataController.objects.filter(bookmarked=True)
        self.assertEqual(links.count(), 1)

        json_file = conf.get_bookmarks_path("2023") / "bookmarks_EN_entries.json"
        self.assertEqual(json_file.exists(), True)

        json_obj = json.loads(json_file.read_text())

        self.assertEqual(len(json_obj), 1)

        json_file = conf.get_bookmarks_path() / "sources.json"
        self.assertEqual(json_file.exists(), True)

    def test_write_source_export_to_cms(self):
        import json

        entry = ConfigurationEntry.get()
        entry.data_export_path = self.test_export_path
        entry.save()

        conf = Configuration.get_object()

        writer = DataWriter(conf)
        writer.write_bookmarks()

        json_file = conf.get_sources_json_path()
        self.assertEqual(json_file.exists(), True)

        json_obj = json.loads(json_file.read_text())

        self.assertEqual(len(json_obj), 1)

    def test_write_daily_data(self):
        import json

        entry = ConfigurationEntry.get()
        entry.data_export_path = self.test_export_path
        entry.save()

        conf = Configuration.get_object()

        writer = DataWriter(conf)
        writer.write_daily_data("2023-03-03")

        json_file = (
            conf.get_daily_data_day_path("2023-03-03") / "https.youtube.com_entries.json"
        )

        json_obj = json.loads(json_file.read_text())

        self.assertEqual(len(json_obj), 2)

        json_file = conf.get_daily_data_path() / "sources.json"
        self.assertEqual(json_file.exists(), True)

        json_file = conf.get_daily_data_path() / "domains.json"
        self.assertEqual(json_file.exists(), True)

    def test_domain_json(self):
        entry = ConfigurationEntry.get()
        entry.data_export_path = self.test_export_path
        entry.save()

        conf = Configuration.get_object()

        writer = DataWriter(conf)
        json = writer.get_domains_json()
        # json as text
        self.assertEqual(len(json), 15)
