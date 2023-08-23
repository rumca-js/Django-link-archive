import traceback
from datetime import timedelta, datetime

from .dateutils import DateUtils
from .models import PersistentInfo, RssSourceExportHistory, ConfigurationEntry
from .controllers import SourceDataController, LinkDataController
from .repotypes import *


class UpdateManager(object):
    def __init__(self, config):
        self._cfg = config

    def write_and_push_to_git(self, input_date=""):
        try:
            if not RssSourceExportHistory.is_update_required():
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

        conf = ConfigurationEntry.get()

        writer = DataWriter(self._cfg)
        writer.write_bookmarks()

        self.push_bookmarks_repo(conf)

    def write_and_push_daily_data(self, input_date=""):
        from .datawriter import DataWriter

        conf = ConfigurationEntry.get()

        write_date = datetime.strptime(input_date, "%Y-%m-%d").date()
        if input_date == "":
            write_date = DateUtils.get_date_yesterday()

        writer = DataWriter(self._cfg)
        writer.write_daily_data(write_date.isoformat())

        self.push_daily_repo(conf, write_date)

        writer.clear_daily_data(write_date.isoformat())

    def push_daily_repo(self, conf, write_date):
        PersistentInfo.create("Pushing to RSS link repo")

        repo = DailyRepo(conf, conf.git_daily_repo)

        repo.up()

        local_dir = self._cfg.get_daily_data_path(write_date.isoformat())
        repo.copy_day_data(local_dir, write_date)
        repo.copy_file(self._cfg.get_bookmarks_path() / "sources.json")

        repo.add([])
        repo.commit(DateUtils.get_dir4date(write_date))
        repo.push()

    def push_bookmarks_repo(self, conf):
        PersistentInfo.create("Pushing main repo data")

        yesterday = DateUtils.get_date_yesterday()

        repo = MainRepo(conf, conf.git_repo)

        repo.up()

        local_dir = self._cfg.get_bookmarks_path()
        repo.copy_main_data(local_dir)

        repo.add([])
        repo.commit(DateUtils.get_dir4date(yesterday))
        repo.push()
