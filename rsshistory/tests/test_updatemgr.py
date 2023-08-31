from pathlib import Path
import shutil
from datetime import datetime

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from ..models import DataExport
from ..controllers import SourceDataController, LinkDataController
from ..updatemgr import UpdateManager
from ..configuration import Configuration
from ..dateutils import DateUtils


class BookmarkTestRepo(object):
    def __init__(self, git_data):
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


class DailyTestRepo(BookmarkTestRepo):
    pass


class RepoTestFactory(object):
    used_repos = []

    def get(export_data):
        if export_data.export_type == DataExport.EXPORT_TYPE_GIT:
           if export_data.export_data == DataExport.EXPORT_DAILY_DATA:
               RepoTestFactory.used_repos.append(RepoTestFactory)
               return DailyTestRepo
           if export_data.export_data == DataExport.EXPORT_BOOKMARKS:
               RepoTestFactory.used_repos.append(RepoTestFactory)
               return BookmarkTestRepo


class UpdateManagerTest(TestCase):

    def setUp(self):
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
        DataExport.objects.create(
                enabled = True,
                export_type = DataExport.EXPORT_TYPE_GIT,
                export_data = DataExport.EXPORT_DAILY_DATA,
                local_path = "test",
                remote_path = "test.git",
                user = "user",
                password = "password",
        )
        DataExport.objects.create(
                enabled = True,
                export_type = DataExport.EXPORT_TYPE_GIT,
                export_data = DataExport.EXPORT_BOOKMARKS,
                local_path = "test",
                remote_path = "test.git",
                user = "user",
                password = "password",
        )

    def test_push_daily_repo(self):
        RepoTestFactory.used_repos = []

        conf = Configuration.get_object() 
        mgr = UpdateManager(conf, RepoTestFactory)

        write_date = DateUtils.get_date_yesterday()

        mgr.push_daily_repo(write_date)
        self.assertTrue(True)

        self.assertEqual(len(RepoTestFactory.used_repos), 1)

    def test_bookmark_repo(self):
        RepoTestFactory.used_repos = []

        conf = Configuration.get_object() 
        mgr = UpdateManager(conf, RepoTestFactory)

        mgr.push_bookmarks_repo()
        self.assertTrue(True)

        self.assertEqual(len(RepoTestFactory.used_repos), 1)
