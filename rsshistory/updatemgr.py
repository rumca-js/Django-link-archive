import traceback
import subprocess
from pathlib import Path
from datetime import timedelta, datetime

from utils.dateutils import DateUtils

from .apps import LinkDatabase
from .models import AppLogging, DataExport
from .controllers import SourceDataController, LinkDataController
from .repositoryfactory import RepositoryFactory
from .datawriter import DataWriter, DataWriterConfiguration


class UpdateExportManager(object):
    """
    This class is a middleman between data writer & repositories
    """

    def __init__(self, config, repo_builder, export_data, date=None):
        self._cfg = config
        self.export_data = export_data
        self.date = date
        self.repo_builder = repo_builder
        self.writer_config = None

    def process(self):
        status = False

        self.write()
        status = self.push()
        self.clear()

        return status

    def write(self):
        AppLogging.notify("Writing to directory: {}".format(self.get_write_directory()))

        if self.date:
            config = DataWriterConfiguration(
                self._cfg,
                self.export_data,
                self.get_write_directory(),
                self.date.isoformat(),
            )
        else:
            config = DataWriterConfiguration(
                self._cfg, self.export_data, self.get_write_directory()
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

        return (
            Path(self._cfg.get_export_path())
            / Path(self.export_data.local_path)
            / directory
        )

    def push(self):
        export_data = self.export_data

        message = "Commit"

        if self.export_data.export_data == DataExport.EXPORT_DAILY_DATA:
            message = DateUtils.get_dir4date(self.date)
        else:
            # TODO maybe use today
            yesterday = DateUtils.get_date_yesterday()
            message = DateUtils.get_dir4date(yesterday)

        repo_class = self.repo_builder.get(export_data)

        repo = repo_class(
            export_data,
            operating_dir=self.get_repo_operating_dir(),
            data_source_dir=self.get_write_directory(),
        )

        if repo.push_to_repo(message):
            return True
        else:
            return False

    def clear(self):
        dir = self.get_write_directory()
        if dir.exists():
            import shutil

            shutil.rmtree(dir)

    def get_repo_operating_dir(self):
        """
        Path to repository, rather absolute
        """
        return self.get_directory() / "repository"

    def get_write_directory(self):
        return self.get_directory() / "write"


class UpdateManager(object):
    def __init__(self, config, repo_builder=None):
        self._cfg = config

        if repo_builder is None:
            self.repo_builder = RepositoryFactory
        else:
            self.repo_builder = repo_builder

    def write_and_push(self, export_data, input_date=""):
        AppLogging.info("Export:{}. Writing and Pushing data".format(export_data.id))

        if input_date == "":
            write_date = DateUtils.get_date_yesterday()
        else:
            write_date = datetime.strptime(input_date, "%Y-%m-%d").date()

        mgr = UpdateExportManager(self._cfg, self.repo_builder, export_data, write_date)
        status = mgr.process()

        if status:
            AppLogging.info(
                "Export:{}. Writing and Pushing data - DONE".format(export_data.id)
            )
        else:
            AppLogging.error(
                "Export:{}. Writing and Pushing data - ERROR".format(export_data.id)
            )

        return status

    def write(self, export_data, input_date=""):
        if input_date == "":
            write_date = DateUtils.get_date_yesterday()
        else:
            write_date = datetime.strptime(input_date, "%Y-%m-%d").date()

        mgr = UpdateExportManager(self._cfg, self.repo_builder, export_data, write_date)
        mgr.write()

        AppLogging.info("Writing data - daily data DONE")
