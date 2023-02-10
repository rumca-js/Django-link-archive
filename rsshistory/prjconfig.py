from pathlib import Path
import logging
import traceback
from datetime import timedelta, datetime, date
from pytz import timezone

from .gitrepo import *

from .threads import *
from .basictypes import *
from .dateutils import DateUtils
from .models import PersistentInfo, RssSourceImportHistory


__version__ = "0.5.0"


class Configuration(object):
   obj = None

   def __init__(self, app_name):
       self.app_name = str(app_name)

       self.directory = Path(".")
       self.version = __version__
       self.server_log_file = self.directory / "log_{0}.txt".format(app_name)

       self.enable_logging()
       self.create_threads()

       print("Creating configuration item")

   def get_object(app_name):
       app_name = str(app_name)
       if not Configuration.obj:
           Configuration.obj = {app_name : Configuration(app_name)}
       if app_name not in Configuration.obj:
           Configuration.obj[app_name] = Configuration(app_name)

       return Configuration.obj[app_name]

   def enable_logging(self, create_file = True):
       self.server_log_file = self.directory / "log_{0}.txt".format(self.app_name)
       self.global_log_file = self.directory / "log_global.txt"

       logging.shutdown()

       self.server_log_file.unlink(True)
       self.global_log_file.unlink(True)

       logging.basicConfig(level=logging.INFO, filename=self.global_log_file, format='[%(asctime)s %(name)s]%(levelname)s:%(message)s')

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
       return  log 

   def get_export_path(self, append = None):
       if append:
           return self.directory / 'exports' / self.app_name / append
       else:
           return self.directory / 'exports' / self.app_name

   def get_import_path(self):
       return self.directory / 'imports' / self.app_name

   def get_data_path(self):
       return self.directory / 'data' / self.app_name

   def get_bookmarks_path(self, append = None):
       if append:
           return self.get_export_path("bookmarks") / append
       else:
           return self.get_export_path("bookmarks")

   def get_sources_json_path(self):
       return self.get_bookmarks_path("sources.json")

   def get_sources_file_name(self):
       return "sources.json"

   def get_daily_data_path(self, day_iso = None):
       if day_iso == None:
           from ..dateutils import DateUtils
           day_iso = DateUtils.get_date_today().isoformat()

       day_path = Path(day_iso)
       entries_dir = self.get_export_path(day_iso)
       return entries_dir

   def create_threads(self):
       download_rss = ThreadJobCommon("process-source")
       refresh_thread = ThreadJobCommon("refresh-thread", 3600, True) #3600 is 1 hour
       wayback = ThreadJobCommon("wayback")
       from .threadhandlers import HandlerManager

       thread_mgr = HandlerManager(self)

       self.threads = [
               download_rss,
               refresh_thread,
               wayback
               ]

       for athread in self.threads:
           athread.set_config(thread_mgr)
           athread.start()

   def get_threads(self):
       return self.threads

   def close(self):
       for athread in self.threads:
           athread.close()

   def download_rss(self, item, force = False):
       if force == False:
           if item.is_fetch_possible() == False:
               return False

       self.threads[0].add_to_process_list(item)
       return True

   def wayback_save(self, url):
       PersistentInfo.create("Wayback save on URL:{0}".format(url))
       self.threads[2].add_to_process_list(url)
       return True

   def get_url_clean_name(self, file_name):
       file_name = file_name.replace(":", ".")\
              .replace("/", "")\
              .replace("\\","")\
              .replace("?",".")\
              .replace("=",".")

       return file_name
