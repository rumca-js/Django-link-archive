import json
from pathlib import Path
from django.contrib.auth.models import User

from utils.dateutils import DateUtils
from utils.services import ReadingList

from ..serializers import MainExporter
from ..controllers import (
    LinkDataController,
)
from ..datawriter import DataWriterConfiguration
from ..configuration import Configuration
from ..models import DataExport

from .fakeinternet import FakeInternetTestCase


class MainExporterTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="test_username", password="testpassword"
        )
        self.create_exports()
        self.create_entries()
        self.setup_configuration()

    def create_exports(self):
        self.export_bookmarks = DataExport.objects.create(
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_DAILY_DATA,
            local_path=".",
            remote_path=".",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=False,
            export_sources=False,
        )
        self.export_permanents = DataExport.objects.create(
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_DAILY_DATA,
            local_path=".",
            remote_path=".",
            export_entries=True,
            export_entries_bookmarks=False,
            export_entries_permanents=True,
            export_sources=False,
        )
        self.export_both = DataExport.objects.create(
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_DAILY_DATA,
            local_path=".",
            remote_path=".",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=True,
            export_sources=False,
        )
        self.export_sources = DataExport.objects.create(
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_DAILY_DATA,
            local_path=".",
            remote_path=".",
            export_entries=False,
            export_entries_bookmarks=True,
            export_entries_permanents=True,
            export_sources=True,
        )

    def create_entries(self):
        """
        domains are permanent, links can be bookmarked
        """
        entry1 = LinkDataController.objects.create(
            link="https://link-1.com/test",
            title="The first link",
            bookmarked=False,
            permanent=False,
        )
        entry2 = LinkDataController.objects.create(
            link="https://link-2.com/test",
            title="The first link",
            bookmarked=True,
            permanent=False,
        )
        entry3 = LinkDataController.objects.create(
            link="https://link-3.com",
            title="The first link",
            bookmarked=False,
            permanent=True,
        )

    def test_main_exporter__bookmarks(self):
        conf = Configuration.get_object()

        data_writer_config = DataWriterConfiguration(
            conf, self.export_bookmarks, Path("./data/test/daily_data")
        )

        exporter = MainExporter(data_writer_config)
        entries = exporter.get_entries()
        self.assertEqual(entries.count(), 1)

    def test_main_exporter__parmanents(self):
        conf = Configuration.get_object()

        data_writer_config = DataWriterConfiguration(
            conf, self.export_permanents, Path("./data/test/daily_data")
        )

        exporter = MainExporter(data_writer_config)
        entries = exporter.get_entries()
        self.assertEqual(entries.count(), 1)

    def test_main_exporter__both(self):
        conf = Configuration.get_object()

        data_writer_config = DataWriterConfiguration(
            conf, self.export_both, Path("./data/test/daily_data")
        )

        exporter = MainExporter(data_writer_config)
        entries = exporter.get_entries()
        self.assertEqual(entries.count(), 2)

    def test_main_exporter__sources(self):
        conf = Configuration.get_object()

        data_writer_config = DataWriterConfiguration(
            conf, self.export_sources, Path("./data/test/daily_data")
        )

        exporter = MainExporter(data_writer_config)
        entries = exporter.get_entries()
        self.assertEqual(entries.count(), 0)
