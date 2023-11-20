from pathlib import Path
import shutil
import json

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from ..models import ConfigurationEntry, PersistentInfo, Domains, DataExport
from ..controllers import SourceDataController, LinkDataController
from ..configuration import Configuration
from ..datawriter import DataWriter, DataWriterConfiguration
from ..dateutils import DateUtils


class DataWriterTest(TestCase):
    def setUp(self):
        self.disable_web_pages()

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
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=nonbookmarked",
            title="The second link",
            source_obj=source_youtube,
            bookmarked=False,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=permanent",
            title="The first link",
            source_obj=source_youtube,
            permanent=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
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

        self.export_daily = DataExport.objects.create(
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_DAILY_DATA,
            local_path=".",
            remote_path=".",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=True,
            export_sources=True,
        )

        self.export_year = DataExport.objects.create(
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_YEAR_DATA,
            local_path=".",
            remote_path=".",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=True,
            export_sources=True,
        )

        self.export_notime = DataExport.objects.create(
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_NOTIME_DATA,
            local_path=".",
            remote_path=".",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=True,
            export_sources=True,
        )

    def tearDown(self):
        self.remove_all_files()

    def disable_web_pages(self):
        from ..webtools import BasePage, Page

        BasePage.user_agent = None
        Page.user_agent = None
        entry = ConfigurationEntry.get()
        entry.user_agent = ""
        entry.save()

    def remove_all_files(self):
        if self.test_export_path.exists():
            shutil.rmtree(self.test_export_path.as_posix())
            shutil.rmtree(self.test_export_path.parent.as_posix())

    def test_domain_json(self):
        entry = ConfigurationEntry.get()
        entry.data_export_path = self.test_export_path
        entry.save()

        conf = Configuration.get_object()

        dw_conf = DataWriterConfiguration(conf, self.export_daily, "daily_data")
        writer = DataWriter.get(dw_conf)

        json_text = writer.get_domains_json()

        json_obj = json.loads(json_text)

        self.assertEqual(len(json_obj), 1)

    def test_sources_json(self):
        entry = ConfigurationEntry.get()
        entry.data_export_path = self.test_export_path
        entry.save()

        conf = Configuration.get_object()

        dw_conf = DataWriterConfiguration(conf, self.export_daily, "daily_data")
        writer = DataWriter.get(dw_conf)

        json_text = writer.get_sources_json()
        json_obj = json.loads(json_text)

        self.assertEqual(len(json_obj), 1)

    def test_write_year(self):
        entry = ConfigurationEntry.get()
        entry.data_export_path = self.test_export_path
        entry.save()

        conf = Configuration.get_object()

        dw_conf = DataWriterConfiguration(conf, self.export_year, "year")
        writer = DataWriter.get(dw_conf)
        writer.write()

        links = LinkDataController.objects.filter(bookmarked=True)
        self.assertEqual(links.count(), 1)

        json_file = (
            conf.get_export_path()
            / self.export_year.local_path
            / "year"
            / "2023"
            / "bookmarks_EN_entries.json"
        )
        print("Test JSON path")
        print(str(json_file))
        self.assertEqual(json_file.exists(), True)

        json_obj = json.loads(json_file.read_text())

        self.assertEqual(len(json_obj), 1)

        json_file = (
            conf.get_export_path()
            / self.export_year.local_path
            / "year"
            / "sources.json"
        )
        self.assertEqual(json_file.exists(), True)

    def test_write_notime(self):
        entry = ConfigurationEntry.get()
        entry.data_export_path = self.test_export_path
        entry.save()

        conf = Configuration.get_object()

        dw_conf = DataWriterConfiguration(conf, self.export_notime, "notime")
        writer = DataWriter.get(dw_conf)
        writer.write()

        links = LinkDataController.objects.filter(bookmarked=True)
        self.assertEqual(links.count(), 1)

        permanent_path = (
            conf.get_export_path()
            / self.export_year.local_path
            / "notime"
            / "permanent"
            / "00000"
        )
        self.assertEqual(permanent_path.exists(), True)

        # json_file = conf.get_export_path() / self.export_year.local_path / "notime" / "permanent" / "bookmarks_EN_entries.json"
        # self.assertEqual(json_file.exists(), True)

        # json_obj = json.loads(json_file.read_text())

        # self.assertEqual(len(json_obj), 1)

        json_file = (
            conf.get_export_path()
            / self.export_year.local_path
            / "notime"
            / "sources.json"
        )
        self.assertEqual(json_file.exists(), True)

    def test_write_daily_data(self):
        entry = ConfigurationEntry.get()
        entry.data_export_path = self.test_export_path
        entry.save()

        conf = Configuration.get_object()

        dw_conf = DataWriterConfiguration(
            conf, self.export_daily, "daily_data", "2023-03-03"
        )
        writer = DataWriter.get(dw_conf)
        writer.write()

        json_file = (
            conf.get_export_path()
            / self.export_year.local_path
            / "daily_data"
            / "2023"
            / "03"
            / "2023-03-03"
            / "https.youtube.com_entries.json"
        )

        json_obj = json.loads(json_file.read_text())

        self.assertEqual(len(json_obj), 3)

        json_file = (
            conf.get_export_path()
            / self.export_year.local_path
            / "daily_data"
            / "sources.json"
        )
        self.assertEqual(json_file.exists(), True)
