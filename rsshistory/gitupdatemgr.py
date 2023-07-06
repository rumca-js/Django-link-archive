import logging
import traceback

from .dateutils import DateUtils
from .models import PersistentInfo, RssSourceExportHistory, ConfigurationEntry
from .prjgitrepo import *


class GitUpdateManager(object):
    def __init__(self, config):
        self._cfg = config

    def write_and_push_to_git(self):
        try:
            if not RssSourceExportHistory.is_update_required():
                return

            conf = ConfigurationEntry.get()
            yesterday = DateUtils.get_date_yesterday()

            PersistentInfo.create("Pushing data to git")

            from .datawriter import DataWriter

            writer = DataWriter(self._cfg)
            writer.write_daily_data(yesterday.isoformat())
            writer.write_bookmarks()
            writer.write_sources()

            self.push_to_git(conf)

            PersistentInfo.create("Pushing data to git: Done")

            new_history = RssSourceExportHistory(date=yesterday)
            new_history.save()

            self.clear_old_entries()

            writer.clear_daily_data(yesterday.isoformat())

        except Exception as e:
            log = logging.getLogger(self._cfg.app_name)
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception during refresh: {0} {1}".format(str(e), error_text)
            )
            log.critical(e, exc_info=True)

    def push_to_git(self, conf):
        self.push_daily_repo(conf)
        self.push_bookmarks_repo(conf)

    def push_daily_repo(self, conf):
        log = logging.getLogger(self._cfg.app_name)
        PersistentInfo.create("Pushing to RSS link repo")

        yesterday = DateUtils.get_date_yesterday()

        repo = DailyRepo(conf, conf.git_daily_repo)

        repo.up()

        local_dir = self._cfg.get_daily_data_path(yesterday.isoformat())
        repo.copy_day_data(local_dir, yesterday)
        repo.copy_file(self._cfg.get_bookmarks_path() / "sources.json")

        repo.add([])
        repo.commit(DateUtils.get_dir4date(yesterday))
        repo.push()

    def push_bookmarks_repo(self, conf):
        log = logging.getLogger(self._cfg.app_name)
        PersistentInfo.create("Pushing main repo data")

        yesterday = DateUtils.get_date_yesterday()

        repo = MainRepo(conf, conf.git_repo)

        repo.up()

        local_dir = self._cfg.get_bookmarks_path()
        repo.copy_main_data(local_dir)

        repo.add([])
        repo.commit(DateUtils.get_dir4date(yesterday))
        repo.push()

    def clear_old_entries(self):
        log = logging.getLogger(self._cfg.app_name)

        from datetime import timedelta
        from .controllers import SourceDataController, LinkDataController

        sources = SourceDataController.objects.all()
        for source in sources:
            if not source.is_removeable():
                continue

            days = source.get_days_to_remove()
            if days > 0:
                current_time = DateUtils.get_datetime_now_utc()
                days_before = current_time - timedelta(days=days)

                entries = LinkDataController.objects.filter(
                    source=source.url, persistent=False, date_published__lt=days_before
                )
                if entries.exists():
                    PersistentInfo.create(
                        "Removing old RSS data for source: {0} {1}".format(
                            source.url, source.title
                        )
                    )
                    entries.delete()
