from pathlib import Path
from django.contrib.auth.models import User

from utils.dateutils import DateUtils

from ..models import DataExport, ConfigurationEntry, UserBookmarks
from ..controllers import SourceDataController, LinkDataController
from ..updatemgr import UpdateManager, UpdateExportManager
from ..configuration import Configuration
from ..apps import LinkDatabase
from ..services import GitRepo

from .fakeinternet import FakeInternetTestCase


class BaseRepo(GitRepo):
    def __init__(self, git_data, operating_dir = None):
        super().__init__(git_data, operating_dir)

        self.is_up = False
        self.is_add = False
        self.is_commit = False
        self.is_push = False
        self.is_copy_tree = False

    def up(self):
        self.is_up = True

    def add(self, files):
        self.is_add = True

    def commit(self, commit_message):
        self.is_commit = True

    def push(self):
        self.is_push = True

    def copy_tree(self, input_path):
        self.is_copy_tree = True


class RepoTestFactory(object):
    used_repos = []

    def get(export_data):
        RepoTestFactory.used_repos.append(BaseRepo)
        return BaseRepo


class UpdateManagerGitTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
            is_staff=True,
        )

        c = Configuration.get_object()
        c.config_entry = ConfigurationEntry.get()

        c.config_entry.accept_not_domain_entries = True
        c.config_entry.data_import_path = "./data/imports"
        c.config_entry.data_export_path = "./data/exports"
        c.config_entry.save()

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )

        entry = LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=bookmarked",
            title="The first link",
            source_obj=source_youtube,
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        date = DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M")
        UserBookmarks.objects.create(
            date_bookmarked=date, user_object=self.user, entry_object=entry
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

        DataExport.objects.create(
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
        DataExport.objects.create(
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
        DataExport.objects.create(
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

    def test_push_daily_repo(self):
        RepoTestFactory.used_repos = []

        conf = Configuration.get_object()
        mgr = UpdateManager(conf, RepoTestFactory)

        export_config = DataExport.objects.filter(
            export_data=DataExport.EXPORT_DAILY_DATA
        )[0]

        mgr.write_and_push(export_config)

        self.assertEqual(len(RepoTestFactory.used_repos), 1)

        # expected_path = Path("./data/exports/daily_dir/git/RSS-Link-Database-DAILY")
        # self.assertEqual(mgr.get_repo_operating_dir(), expected_path)

    def test_year_repo(self):
        RepoTestFactory.used_repos = []

        conf = Configuration.get_object()
        mgr = UpdateManager(conf, RepoTestFactory)

        export_config = DataExport.objects.filter(
            export_data=DataExport.EXPORT_YEAR_DATA
        )[0]

        mgr.write_and_push(export_config)
        self.assertEqual(len(RepoTestFactory.used_repos), 1)

        # expected_path = Path("./data/exports/year_dir/git/RSS-Link-Database-YEAR")
        # self.assertEqual(mgr.get_repo_operating_dir(), expected_path)

    def test_notime_repo(self):
        RepoTestFactory.used_repos = []

        conf = Configuration.get_object()
        mgr = UpdateManager(conf, RepoTestFactory)

        export_config = DataExport.objects.filter(
            export_data=DataExport.EXPORT_NOTIME_DATA
        )[0]

        mgr.write_and_push(export_config)

        self.assertEqual(len(RepoTestFactory.used_repos), 1)

        # expected_path = Path("./data/exports/notime_dir/git/RSS-Link-Database-NOTIME")
        # self.assertEqual(mgr.get_repo_operating_dir(), expected_path)


class UpdateManagerLocTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
            is_staff=True,
        )

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )

        entry = LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=bookmarked",
            title="The first link",
            source_obj=source_youtube,
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        date = DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M")
        UserBookmarks.objects.create(
            date_bookmarked=date, user_object=self.user, entry_object=entry
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

        DataExport.objects.create(
            enabled=True,
            export_type=DataExport.EXPORT_TYPE_LOC,
            export_data=DataExport.EXPORT_DAILY_DATA,
            local_path="test",
            remote_path="test.git",
            user="testuser",
            password="password",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=True,
            export_sources=True,
        )
        DataExport.objects.create(
            enabled=True,
            export_type=DataExport.EXPORT_TYPE_LOC,
            export_data=DataExport.EXPORT_YEAR_DATA,
            local_path="test",
            remote_path="test.git",
            user="testuser",
            password="password",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=True,
            export_sources=True,
        )
        DataExport.objects.create(
            enabled=True,
            export_type=DataExport.EXPORT_TYPE_LOC,
            export_data=DataExport.EXPORT_NOTIME_DATA,
            local_path="test",
            remote_path="test.git",
            user="testuser",
            password="password",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=True,
            export_sources=True,
        )

    def test_push_daily_repo(self):
        RepoTestFactory.used_repos = []

        conf = Configuration.get_object()
        mgr = UpdateManager(conf, RepoTestFactory)

        # write_date = DateUtils.get_date_yesterday()

        export_config = DataExport.objects.filter(
            export_data=DataExport.EXPORT_DAILY_DATA
        )[0]

        mgr.write_and_push(export_config)

        self.assertEqual(len(RepoTestFactory.used_repos), 0)

    def test_year_repo(self):
        RepoTestFactory.used_repos = []

        conf = Configuration.get_object()
        mgr = UpdateManager(conf, RepoTestFactory)

        export_config = DataExport.objects.filter(
            export_data=DataExport.EXPORT_YEAR_DATA
        )[0]

        mgr.write_and_push(export_config)
        self.assertEqual(len(RepoTestFactory.used_repos), 0)

    def test_notime_repo(self):
        RepoTestFactory.used_repos = []

        conf = Configuration.get_object()
        mgr = UpdateManager(conf, RepoTestFactory)

        export_config = DataExport.objects.filter(
            export_data=DataExport.EXPORT_NOTIME_DATA
        )[0]

        mgr.write_and_push(export_config)

        self.assertEqual(len(RepoTestFactory.used_repos), 0)


class UpdateExportManagerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        DataExport.objects.create(
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
        DataExport.objects.create(
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
        DataExport.objects.create(
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

    def test_get_directory__notime(self):

        config = Configuration.get_object()
        export_config = DataExport.objects.filter(
            export_data=DataExport.EXPORT_NOTIME_DATA
        )[0]

        mgr = UpdateExportManager(config, RepoTestFactory, export_config)

        expected_path = Path(config.config_entry.data_export_path) / LinkDatabase.name / Path("./notime_dir") / "notime_data"

        # call tested function
        self.assertEqual(mgr.get_directory(), expected_path)
        self.assertEqual(mgr.get_directory(), expected_path)

    def test_get_repo_operating_dir(self):

        config = Configuration.get_object()
        export_config = DataExport.objects.filter(
            export_data=DataExport.EXPORT_DAILY_DATA
        )[0]

        mgr = UpdateExportManager(config, RepoTestFactory, export_config)

        expected_path = Path(config.config_entry.data_export_path) / LinkDatabase.name / Path("./daily_dir")  / "daily_data" / "git"

        # call tested function
        self.assertEqual(mgr.get_repo_operating_dir(), expected_path)

    def test_get_write_directory(self):

        config = Configuration.get_object()
        export_config = DataExport.objects.filter(
            export_data=DataExport.EXPORT_DAILY_DATA
        )[0]

        mgr = UpdateExportManager(config, RepoTestFactory, export_config)

        expected_path = Path(config.config_entry.data_export_path) / LinkDatabase.name / Path("./daily_dir")  / "daily_data" / "write"

        # call tested function
        self.assertEqual(mgr.get_write_directory(), expected_path)
