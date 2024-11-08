from pathlib import Path
from django.contrib.auth.models import User

from utils.dateutils import DateUtils
from utils.services import ReadingList

from ..serializers import EntryDailyDataMainExporter
from ..models import DataExport
from ..controllers import LinkDataController
from ..configuration import Configuration
from ..datawriter import DataWriterConfiguration

from .fakeinternet import FakeInternetTestCase


class EntryDailyDataMainExporterTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.export = DataExport.objects.create(
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_YEAR_DATA,
            local_path=".",
            remote_path=".",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=False,
            export_sources=True,
        )

        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
            is_staff=True,
        )

        self.create_exports()
        self.create_entries()

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
        LinkDataController.objects.create(
            link="https://link-1.com",
            title="The first link",
            bookmarked=False,
            permanent=False,
            date_published = DateUtils.from_string("2024-12-08T05:29:52Z")
        )
        LinkDataController.objects.create(
            link="https://link-2.com",
            title="The first link",
            bookmarked=True,
            permanent=False,
            date_published = DateUtils.from_string("2024-12-08T05:29:52Z")
        )
        LinkDataController.objects.create(
            link="https://link-3.com",
            title="The first link",
            bookmarked=False,
            permanent=True,
            date_published = DateUtils.from_string("2024-12-08T05:29:52Z")
        )

    def test_bookmarks(self):
        conf = Configuration.get_object().config_entry

        day_iso = "2024-12-08"

        data_writer_config = DataWriterConfiguration(
            conf, self.export_bookmarks, Path("./data/test/daily_data")
        )

        # call tested function
        exporter = EntryDailyDataMainExporter(data_writer_config, day_iso)

        entries = exporter.get_entries()
        self.assertEqual(entries.count(), 1)
