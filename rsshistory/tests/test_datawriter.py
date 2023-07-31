from pathlib import Path
import shutil
from datetime import datetime

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from ..models import ConfigurationEntry, PersistentInfo
from ..controllers import SourceDataController, LinkDataController
from ..prjconfig import Configuration
from ..datawriter import DataWriter


class DataWriterTest(TestCase):
    def setUp(self):
        self.test_export_path = Path("./test_data/exports")
        if self.test_export_path.exists():
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
            link="https://youtube.com?v=persistent",
            title="The first link",
            source_obj=source_youtube,
            persistent=True,
            date_published=datetime.strptime("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=nonpersistent",
            title="The second link",
            source_obj=source_youtube,
            persistent=False,
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

    def tearDown(self):
        self.remove_all_files()

    def remove_all_files(self):
        shutil.rmtree(self.test_export_path.as_posix())
        shutil.rmtree(self.test_export_path.parent.as_posix())

    def test_write_bookmarks(self):
        entry = ConfigurationEntry.get()
        entry.data_export_path = self.test_export_path
        entry.save()

        conf = Configuration.get_object()

        writer = DataWriter(conf)
        writer.write_bookmarks()

        links = LinkDataController.objects.filter(persistent=True)
        self.assertEqual(len(links), 1)

        json_file = conf.get_bookmarks_path("2023") / "bookmarks_EN_entries.json"
        self.assertEqual(json_file.exists(), True)

        import json

        json_obj = json.loads(json_file.read_text())

        self.assertEqual(len(json_obj), 1)

    def test_write_source_export_to_cms(self):
        entry = ConfigurationEntry.get()
        entry.data_export_path = self.test_export_path
        entry.save()

        conf = Configuration.get_object()

        writer = DataWriter(conf)
        writer.write_bookmarks()

        json_file = conf.get_sources_json_path()
        self.assertEqual(json_file.exists(), True)

        import json

        json_obj = json.loads(json_file.read_text())

        self.assertEqual(len(json_obj), 1)

    def test_write_daily_data(self):
        entry = ConfigurationEntry.get()
        entry.data_export_path = self.test_export_path
        entry.save()

        conf = Configuration.get_object()

        writer = DataWriter(conf)
        writer.write_daily_data("2023-03-03")

        json_file = (
            conf.get_daily_data_path("2023-03-03") / "https.youtube.com_entries.json"
        )

        import json

        json_obj = json.loads(json_file.read_text())

        self.assertEqual(len(json_obj), 2)
