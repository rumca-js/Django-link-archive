from pathlib import Path

from django.contrib.auth.models import User
from utils.dateutils import DateUtils
from utils.services import GitRepository

from ..models import DataExport, ConfigurationEntry, UserBookmarks
from ..controllers import SourceDataController, LinkDataController
from ..updatemgr import UpdateManager, UpdateExportManager
from ..configuration import Configuration
from ..apps import LinkDatabase

from .fakeinternet import FakeInternetTestCase


class GitRepositoryTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
            is_staff=True,
        )

        c = Configuration.get_object()
        c.config_entry = ConfigurationEntry.get()

        c.config_entry.accept_non_domain_links = True
        c.config_entry.data_import_path = "./data/imports"
        c.config_entry.data_export_path = "./data/exports"
        c.config_entry.save()

        DataExport.objects.create(
            enabled=True,
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_DAILY_DATA,
            local_path="./daily_dir",
            remote_path="https://github.com/rumca-js/RSS-Link-Database-DAILY.git",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=True,
            export_sources=True,
        )
        DataExport.objects.create(
            enabled=True,
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_YEAR_DATA,
            local_path="./year_dir",
            remote_path="https://github.com/rumca-js/RSS-Link-Database-YEAR.git",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=True,
            export_sources=True,
        )
        DataExport.objects.create(
            enabled=True,
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_NOTIME_DATA,
            local_path="./notime_dir",
            remote_path="https://github.com/rumca-js/RSS-Link-Database-NOTIME.git",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=True,
            export_sources=True,
        )

        DataExport.objects.create(
            enabled=True,
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_NOTIME_DATA,
            local_path="./notime_dir",
            remote_path="https://github.com/rumca-js/RSS-Link-Database-NOTIME",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=True,
            export_sources=True,
        )

    def test_get_repo_name(self):
        export_config = DataExport.objects.filter(
            export_data=DataExport.EXPORT_DAILY_DATA,
            remote_path="https://github.com/rumca-js/RSS-Link-Database-DAILY.git",
        )[0]

        git = GitRepository(export_config)

        # call tested function
        self.assertEqual(git.get_repo_name(), "RSS-Link-Database-DAILY")

    def test_get_repo_name__nogit(self):
        export_config = DataExport.objects.filter(
            export_data=DataExport.EXPORT_NOTIME_DATA,
            remote_path="https://github.com/rumca-js/RSS-Link-Database-NOTIME",
        )[0]

        git = GitRepository(export_config)

        # call tested function
        self.assertEqual(git.get_repo_name(), "RSS-Link-Database-NOTIME")

    def test_get_operating_dir__default(self):
        export_config = DataExport.objects.filter(
            export_data=DataExport.EXPORT_DAILY_DATA
        )[0]
        app = LinkDatabase.name

        git = GitRepository(export_config)

        # call tested function
        self.assertEqual(git.get_operating_dir(), Path("./daily_dir"))

    def test_get_operating_dir__non_default(self):
        export_config = DataExport.objects.filter(
            export_data=DataExport.EXPORT_DAILY_DATA
        )[0]
        app = LinkDatabase.name

        git = GitRepository(
            export_config, operating_dir=Path("./other") / "path" / app / "location"
        )

        # call tested function
        self.assertEqual(
            git.get_operating_dir(), Path("./other") / "path" / app / "location"
        )

    def test_get_local_dir(self):
        export_config = DataExport.objects.filter(
            export_data=DataExport.EXPORT_DAILY_DATA
        )[0]
        app = LinkDatabase.name

        git = GitRepository(
            export_config, operating_dir=Path("./other") / "path" / app / "location"
        )

        # call tested function
        self.assertEqual(
            git.get_local_dir(),
            Path("./other") / "path" / app / "location" / "RSS-Link-Database-DAILY",
        )
