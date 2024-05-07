from ..models import SourceExportHistory
from ..models import DataExport
from datetime import date, timedelta
import datetime

from .fakeinternet import FakeInternetTestCase


class SourceExportHistoryTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def create_exports(self):
        self.export1 = DataExport.objects.create(
            enabled=True,
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_DAILY_DATA,
            local_path="./daily_dir",
            remote_path="https://github.com/rumca-js/RSS-Link-Database-DAILY.git",
            user="testuser",
            password="password",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=True,
            export_sources=True,
        )
        self.export2 = DataExport.objects.create(
            enabled=True,
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_YEAR_DATA,
            local_path="./year_dir",
            remote_path="https://github.com/rumca-js/RSS-Link-Database-YEAR.git",
            user="testuser",
            password="password",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=True,
            export_sources=True,
        )
        self.export3 = DataExport.objects.create(
            enabled=True,
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_NOTIME_DATA,
            local_path="./notime_dir",
            remote_path="https://github.com/rumca-js/RSS-Link-Database-NOTIME.git",
            user="testuser",
            password="password",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=True,
            export_sources=True,
        )

    def test_cleanup(self):
        self.create_exports()

        date = datetime.date.today() - timedelta(days=100)
        SourceExportHistory.objects.create(date = date, export_obj=self.export1)

        # call tested function
        SourceExportHistory.cleanup()

        self.assertEqual(SourceExportHistory.objects.count(), 0)

    def test_is_update_required_true(self):
        SourceExportHistory.objects.all().delete()
        self.create_exports()

        export = DataExport.objects.all()[0]

        # call tested function
        status = SourceExportHistory.is_update_required(export)

        self.assertTrue(status)

    def test_is_update_required(self):
        SourceExportHistory.objects.all().delete()
        self.create_exports()

        export = DataExport.objects.all()[0]
        SourceExportHistory.confirm(export)

        # call tested function
        status = SourceExportHistory.is_update_required(export)

        self.assertFalse(status)
