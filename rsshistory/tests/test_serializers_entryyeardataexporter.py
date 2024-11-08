from pathlib import Path
from django.contrib.auth.models import User

from utils.dateutils import DateUtils
from utils.services import ReadingList

from ..serializers import EntryYearDataMainExporter
from ..models import UserBookmarks, DataExport
from ..controllers import LinkDataController
from ..configuration import Configuration
from ..datawriter import DataWriterConfiguration

from .fakeinternet import FakeInternetTestCase


class EntryYearDataMainExporterTest(FakeInternetTestCase):
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

    def test_bookmarks_for_user_none(self):
        config = Configuration.get_object().config_entry

        date = DateUtils.from_string("2024-12-08T05:29:52Z")

        entry = LinkDataController.objects.create(
            source_url="",
            link="https://linkedin.com",
            title="my title",
            description="my description",
            bookmarked=True,
            language="pl",
            domain=None,
            date_published=date,
            thumbnail="thumbnail",
        )

        dw_conf = DataWriterConfiguration(config, self.export, Path("./data/test/year"))

        # call tested function
        exporter = EntryYearDataMainExporter(dw_conf, self.user)

        entries = exporter.get_entries(2024)
        self.assertEqual(entries.count(), 0)

    def test_bookmarks_for_user_one(self):
        config = Configuration.get_object().config_entry

        date = DateUtils.from_string("2024-12-08T05:29:52Z")

        entry = LinkDataController.objects.create(
            source_url="",
            link="https://linkedin.com",
            title="my title",
            description="my description",
            bookmarked=True,
            language="pl",
            domain=None,
            date_published=date,
            thumbnail="thumbnail",
        )

        bookmark = UserBookmarks.objects.create(
            date_bookmarked=date, user=self.user, entry=entry
        )

        dw_conf = DataWriterConfiguration(config, self.export, Path("./data/test/year"))

        exporter = EntryYearDataMainExporter(dw_conf, self.user)

        # call tested function
        entries = exporter.get_entries(2024)
        self.assertEqual(entries.count(), 1)

    def test_bookmarks_for_no_user(self):
        config = Configuration.get_object().config_entry

        date = DateUtils.from_string("2024-12-08T05:29:52Z")

        entry = LinkDataController.objects.create(
            source_url="",
            link="https://linkedin.com",
            title="my title",
            description="my description",
            bookmarked=True,
            language="pl",
            domain=None,
            date_published=date,
            thumbnail="thumbnail",
        )

        bookmark = UserBookmarks.objects.create(
            date_bookmarked=date, user=self.user, entry=entry
        )

        dw_conf = DataWriterConfiguration(config, self.export, Path("./data/test/year"))

        exporter = EntryYearDataMainExporter(dw_conf, user=None)

        # call tested function
        entries = exporter.get_entries(2024)
        self.assertEqual(entries.count(), 1)
