import traceback
from pathlib import Path
from datetime import timedelta, datetime

from utils.dateutils import DateUtils

from .apps import LinkDatabase
from .models import AppLogging, DataExport
from .controllers import SourceDataController, LinkDataController
from .repotypes import *
from .datawriter import DataWriter, DataWriterConfiguration


class RepoFactory(object):
    def get(export_data):
        if export_data.export_type == DataExport.EXPORT_TYPE_GIT:
            return DefaultRepo

        # TODO add support for more repo types. SMB?


class UpdateExportManager(object):
    def __init__(self, config, repo_builder, export_data, date=None):
        self._cfg = config
        self.export_data = export_data
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
                self._cfg, self.export_data, self.get_directory(), self.date.isoformat()
            )
        else:
            config = DataWriterConfiguration(
                self._cfg, self.export_data, self.get_directory()
            )

        self.writer_config = config

        writer = DataWriter.get(config)
        writer.write()

    def get_directory(self):
        """
        Path to place where data are written to.
        Different types have to occupy different directories,
        because we do not want different exports to change other exports data
        """
        if self.export_data.export_data == DataExport.EXPORT_DAILY_DATA:
            directory = "daily_data"
        elif self.export_data.export_data == DataExport.EXPORT_YEAR_DATA:
            directory = "yearly_data"
        elif self.export_data.export_data == DataExport.EXPORT_NOTIME_DATA:
            directory = "notime_data"

        app = LinkDatabase.name

        return Path(self._cfg.get_export_path()) / Path(self.export_data.local_path) / directory

    def get_repo_operating_dir(self, repo):
        """
        Path to repository, rather absolute
        """
        return self.get_directory() / "git"

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

    def clear_operating_directory(self, repo):
        dir = self.get_repo_operating_dir(repo)
        if dir.exists():
            import shutil

            shutil.rmtree(dir)

    def push_implementation(self, export_data, commit_message):
        AppLogging.info("Pushing repo")

        if export_data.export_type == DataExport.EXPORT_TYPE_GIT:
            repo_class = self.repo_builder.get(export_data)
            repo = repo_class(export_data)

            operating_dir = self.get_repo_operating_dir(repo)
            repo.set_operating_dir(operating_dir)

            repo_is_up = False
            try:
                repo.up()
                repo_is_up = True
            except Exception as E:
                AppLogging.exc(
                    E,
                    "Cannot update repository, removing directory {}".format(
                        operating_dir
                    ),
                )
                self.clear_operating_directory(repo)

            if repo_is_up:
                local_dir = self.get_directory()
                repo.copy_tree(local_dir)

                repo.add([])
                if repo.commit(commit_message) == 0:
                    repo.push()

                    return True
        elif export_data.export_type == DataExport.EXPORT_TYPE_LOC:
            if export_data.local_path == export_data.remote_path:
                return
            if export_data.remote_path is None or export_data.remote_path == "":
                return

            # TODO implement

            return True

        AppLogging.info("Pushing repo done")
        return False


class UpdateManager(object):
    def __init__(self, config, repo_builder=None):
        self._cfg = config

        if repo_builder is None:
            self.repo_builder = RepoFactory
        else:
            self.repo_builder = repo_builder

    def write_and_push(self, export_data, input_date=""):
        AppLogging.info("Export:{}. Writing and Pushing data".format(export_data.id))

        if input_date == "":
            write_date = DateUtils.get_date_yesterday()
        else:
            write_date = datetime.strptime(input_date, "%Y-%m-%d").date()

        mgr = UpdateExportManager(
            self._cfg, self.repo_builder, export_data, write_date
        )
        mgr.process()

        AppLogging.info(
            "Export:{}. Writing and Pushing data - DONE".format(export_data.id)
        )

    def write(self, export_data, input_date=""):
        if input_date == "":
            write_date = DateUtils.get_date_yesterday()
        else:
            write_date = datetime.strptime(input_date, "%Y-%m-%d").date()

        mgr = UpdateExportManager(
            self._cfg, self.repo_builder, export_data, write_date
        )
        mgr.write()

        AppLogging.info("Writing data - daily data DONE")
