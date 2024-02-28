import traceback
from pathlib import Path
from datetime import timedelta, datetime

from .dateutils import DateUtils
from .models import PersistentInfo, SourceExportHistory, DataExport
from .controllers import SourceDataController, LinkDataController
from .repotypes import *
from .datawriter import DataWriter, DataWriterConfiguration


class RepoFactory(object):
    def get(export_data):
        if export_data.export_type == DataExport.EXPORT_TYPE_GIT:
            return DefaultRepo

        # TODO add support for more repo types. SMB?


class UpdateExportManager(object):
    def __init__(self, config, repo_builder, export_data, directory=None, date=None):
        self._cfg = config
        self.export_data = export_data
        self.directory = directory
        self.date = date
        self.repo_builder = repo_builder
        self.writer_config = None

    def process(self):
        self.write()
        self.push()
        self.clear()

    def write(self):
        if self.date:
            config = DataWriterConfiguration(
                self._cfg, self.export_data, self.directory, self.date.isoformat()
            )
        else:
            config = DataWriterConfiguration(
                self._cfg, self.export_data, self.directory
            )

        self.writer_config = config

        writer = DataWriter.get(config)
        writer.write()

    def get_directory(self):
        return Path(self.export_data.local_path) / self.directory

    def get_repo_operating_dir(self, repo):
        return Path(self._cfg.get_export_path()) / self.export_data.local_path / "git" / repo.get_repo_name()

    def push(self):
        export_data = self.export_data

        if self.export_data.export_data == DataExport.EXPORT_DAILY_DATA:
            message = DateUtils.get_dir4date(self.date)
            self.push_implementation(export_data, message)
        else:
            # TODO maybe use today
            yesterday = DateUtils.get_date_yesterday()
            message = DateUtils.get_dir4date(yesterday)
            self.push_implementation(export_data, message)

    def clear(self):
        dir = self.get_directory()
        if dir.exists():
            import shutil

            shutil.rmtree(dir)

    def push_implementation(self, export_data, commit_message):
        PersistentInfo.create("Pushing repo")

        if export_data.export_type == DataExport.EXPORT_TYPE_GIT:
            repo_class = self.repo_builder.get(export_data)
            repo = repo_class(export_data)

            operating_dir = self.get_repo_operating_dir(repo)
            repo.set_local_dir(operating_dir)

            repo.up()

            local_dir = self._cfg.get_export_path(self.get_directory())
            repo.copy_tree(local_dir)

            repo.add([])
            repo.commit(commit_message)
            repo.push()
        elif export_data.export_type == DataExport.EXPORT_TYPE_LOC:
            if export_data.local_path == export_data.remote_path:
                return
            if export_data.remote_path is None or export_data.remote_path == "":
                return

        PersistentInfo.create("Pushing repo done")


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

            self.write_and_push_notime_data()
            self.write_and_push_year_data()
            self.write_and_push_daily_data(input_date)

            PersistentInfo.create("Pushing data to git: Done")

        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception during refresh: {0} {1}".format(str(e), error_text)
            )

    def write_and_push_daily_data(self, input_date=""):
        PersistentInfo.create("Pushing data to git - daily data")

        if input_date == "":
            write_date = DateUtils.get_date_yesterday()
        else:
            write_date = datetime.strptime(input_date, "%Y-%m-%d").date()

        all_export_data = DataExport.objects.filter(
            export_data=DataExport.EXPORT_DAILY_DATA, enabled=True
        )

        for export_data in all_export_data:
            mgr = UpdateExportManager(
                self._cfg, self.repo_builder, export_data, "daily_data", write_date
            )
            mgr.process()

        PersistentInfo.create("Pushing data to git - daily data - DONE")

    def write_and_push_year_data(self):
        PersistentInfo.create("Pushing data to git - year data")

        all_export_data = DataExport.objects.filter(
            export_data=DataExport.EXPORT_YEAR_DATA, enabled=True
        )

        for export_data in all_export_data:
            mgr = UpdateExportManager(self._cfg, self.repo_builder, export_data, "year")
            mgr.process()

        PersistentInfo.create("Pushing data to git - year data - DONE")

    def write_and_push_notime_data(self):
        PersistentInfo.create("Pushing data to git - notime data")

        all_export_data = DataExport.objects.filter(
            export_data=DataExport.EXPORT_NOTIME_DATA, enabled=True
        )

        for export_data in all_export_data:
            mgr = UpdateExportManager(
                self._cfg, self.repo_builder, export_data, "notime"
            )
            mgr.process()

        PersistentInfo.create("Pushing data to git - notime data - DONE")
