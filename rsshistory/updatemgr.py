import traceback
from datetime import timedelta, datetime

from .dateutils import DateUtils
from .models import PersistentInfo, SourceExportHistory, ConfigurationEntry, DataExport
from .controllers import SourceDataController, LinkDataController
from .repotypes import *


class RepoFactory(object):
    def get(export_data):
        if export_data.export_type == DataExport.EXPORT_TYPE_GIT:
            if export_data.export_data == DataExport.EXPORT_DAILY_DATA:
                return DailyRepo
            if export_data.export_data == DataExport.EXPORT_BOOKMARKS:
                return BookmarkRepo


class UpdateManager(object):
    def __init__(self, config, repo_builder=None):
        self._cfg = config

        if repo_builder is None:
            self.repo_builder = RepoFactory
        else:
            self.repo_builder = repo_builder

    def write_and_push_to_git(self, input_date=""):
        try:
            if not SourceExportHistory.is_update_required():
                return

            PersistentInfo.create("Pushing data to git")

            self.write_and_push_bookmarks()
            self.write_and_push_daily_data(input_date)

            PersistentInfo.create("Pushing data to git: Done")

        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception during refresh: {0} {1}".format(str(e), error_text)
            )

    def write_and_push_bookmarks(self):
        from .datawriter import DataWriter

        writer = DataWriter(self._cfg)
        writer.write_bookmarks()

        self.push_bookmarks_repo()

    def write_and_push_daily_data(self, input_date=""):
        from .datawriter import DataWriter

        if input_date == "":
            write_date = DateUtils.get_date_yesterday()
        else:
            write_date = datetime.strptime(input_date, "%Y-%m-%d").date()

        writer = DataWriter(self._cfg)
        writer.write_daily_data(write_date.isoformat())

        self.push_daily_repo(write_date)

        writer.clear_daily_data(write_date.isoformat())

    def push_daily_repo(self, write_date):
        PersistentInfo.create("Pushing to daily data repo")

        all_export_data = DataExport.objects.filter(
            export_data=DataExport.EXPORT_DAILY_DATA
        )

        for export_data in all_export_data:
            repo_class = self.repo_builder.get(export_data)
            repo = repo_class(export_data)

            repo.up()

            local_dir = self._cfg.get_daily_data_path()
            repo.copy_tree(local_dir)

            repo.add([])
            repo.commit(DateUtils.get_dir4date(write_date))
            repo.push()

        PersistentInfo.create("Pushing to daily data repo done")

    def push_bookmarks_repo(self):
        PersistentInfo.create("Pushing bookmarks repo")

        all_export_data = DataExport.objects.filter(
            export_data=DataExport.EXPORT_BOOKMARKS
        )

        for export_data in all_export_data:
            if export_data.export_type == DataExport.EXPORT_TYPE_GIT:
                yesterday = DateUtils.get_date_yesterday()

                repo_class = self.repo_builder.get(export_data)
                repo = repo_class(export_data)

                repo.up()

                local_dir = self._cfg.get_bookmarks_path()
                repo.copy_tree(local_dir)

                repo.add([])
                repo.commit(DateUtils.get_dir4date(yesterday))
                repo.push()

        PersistentInfo.create("Pushing to bookmarks repo done")
