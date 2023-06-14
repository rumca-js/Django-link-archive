from datetime import datetime
from pathlib import Path
import logging

from .basictypes import *
from .models import ConfigurationEntry


""" version is split into three digits:
 - release
 - model version
 - patch

 if there is a small incremental change bump up the patch number
 if a change requires the model to be changed, then second digit is updated, patch is set to 0
 if something should be released to public, then release version changes
"""
__version__ = "0.10.2"


class Configuration(object):
    obj = {}

    def __init__(self, app_name):
        self.app_name = str(app_name)
        self.thread_mgr = None
        self.directory = Path(".")
        self.version = __version__

        self.enable_logging()

    def get_object(app_name):
        app_name = str(app_name)

        if app_name not in Configuration.obj:
            c = Configuration(app_name)
            Configuration.obj[app_name] = c

        return Configuration.obj[app_name]

    def enable_logging(self, create_file=True):
        self.server_log_file = self.directory / "log_{0}.txt".format(self.app_name)
        self.global_log_file = self.directory / "log_global.txt"

        logging.shutdown()

        self.server_log_file.unlink(True)
        self.global_log_file.unlink(True)

        logging.basicConfig(level=logging.INFO, filename=self.global_log_file,
                            format='[%(asctime)s %(name)s]%(levelname)s:%(message)s')

        # create logger for prd_ci
        log = logging.getLogger(self.app_name)
        log.setLevel(level=logging.INFO)

        # create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        if create_file:
            # create file handler for logger.
            fh = logging.FileHandler(self.server_log_file)
            fh.setLevel(level=logging.DEBUG)
            fh.setFormatter(formatter)
        # reate console handler for logger.
        ch = logging.StreamHandler()
        ch.setLevel(level=logging.DEBUG)
        ch.setFormatter(formatter)

        # add handlers to logger.
        if create_file:
            log.addHandler(fh)

        log.addHandler(ch)
        return log

    def create_threads(self):
        if self.thread_mgr is None:
            from .threadhandlers import HandlerManager
            self.thread_mgr = HandlerManager(self)

    def get_threads(self):
        if self.thread_mgr:
           return self.thread_mgr.threads

    def close(self):
        self.thread_mgr.close()

    def get_export_path(self, append=False):
        directory = Path(ConfigurationEntry.get().data_export_path)
        if append:
            return directory / self.app_name / append
        else:
            return directory / self.app_name

    def get_import_path(self, append=False):
        directory = Path(ConfigurationEntry.get().data_import_path)
        if append:
            return directory / self.app_name / append
        else:
            return directory / self.app_name

    def get_data_path(self):
        return self.directory / 'data' / self.app_name

    def get_bookmarks_path(self, append=None):
        if append:
            return self.get_export_path("bookmarks") / append
        else:
            return self.get_export_path("bookmarks")

    def get_sources_json_path(self):
        return self.get_bookmarks_path("sources.json")

    def get_sources_file_name(self):
        return "sources.json"

    def get_daily_data_path(self, day_iso=None):
        from .dateutils import DateUtils

        if day_iso == None:
            day_iso = DateUtils.get_date_today().isoformat()

        in_date = datetime.fromisoformat(day_iso)
        in_tuple = DateUtils.get_date_tuple(in_date)

        day_path = Path(in_tuple[0]) / in_tuple[1] / Path(day_iso)
        entries_dir = self.get_export_path(day_path)
        return entries_dir

    def get_url_clean_name(self, file_name):
        file_name = file_name.replace(":", ".") \
            .replace("/", "") \
            .replace("\\", "") \
            .replace("?", ".") \
            .replace("=", ".")

        return file_name
