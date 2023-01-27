from pathlib import Path
import time
import shutil
import logging
import traceback
from datetime import timedelta, datetime, date
from pytz import timezone

from .gitrepo import *

from .threads import *
from .basictypes import *
from .dateutils import DateUtils
from .models import PersistentInfo, RssSourceExportHistory, RssSourceImportHistory
from .sources.basepluginbuilder import BasePluginBuilder


__version__ = "0.4.3"


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

   def get_export_path(self):
       return self.directory / 'exports' / self.app_name

   def get_import_path(self):
       return self.directory / 'imports' / self.app_name

   def get_data_path(self):
       return self.directory / 'data' / self.app_name

   def create_threads(self):
       download_rss = ThreadJobCommon("process-source")
       refresh_thread = ThreadJobCommon("refresh-thread", 3600, True) #3600 is 1 hour
       wayback = ThreadJobCommon("wayback")

       self.threads = [
               download_rss,
               refresh_thread,
               wayback
               ]

       for athread in self.threads:
           athread.set_config(self)
           athread.start()

   def get_threads(self):
       return self.threads

   def close(self):
       for athread in self.threads:
           athread.close()

   def t_process_item(self, thread, item):
      from datetime import date, timedelta
      from .sources.rsssourceprocessor import RssSourceProcessor

      if thread == "process-source":
          try:
             proc = RssSourceProcessor(self)
             proc.process_source(item)

             if len(RssSourceImportHistory.objects.filter(url = item.url, date = date.today())) == 0:
                 history = RssSourceImportHistory(url = item.url, date = date.today(), source_obj = item)
                 history.save()

             today = DateUtils.get_iso_today()
             if not item.export_to_cms:
                return

             self.write_files_for_source_for_day(item.url, today)
          except Exception as e:
             log = logging.getLogger(self.app_name)
             PersistentInfo.error("Exception during parsing page contents {0} {1}".format(item.url, str(e)) )
             log.critical(e, exc_info=True)
      elif thread == "refresh-thread":
         try:
             self.t_refresh(item)
         except Exception as e:
            log = logging.getLogger(self.app_name)
            if item:
                log.error("Exception during refreshing {0}".format(item.url) )
            log.critical(e, exc_info=True)
      elif thread == "wayback":
         from .sources.waybackmachine import WaybackMachine
         wb = WaybackMachine()
         wb.save(item)
      else:
         log = logging.getLogger(self.app_name)
         PersistentInfo.error("Not implemented processing thread {0}".format(thread))
         log.critical(e, exc_info=True)
         raise NotImplemented

   def write_files_for_source_for_day(self, source_url, day_iso):
       from .models import RssSourceEntryDataModel
       from .converters import EntriesExporter

       date_range = DateUtils.get_range4day(day_iso)
       entries = RssSourceEntryDataModel.objects.filter(source = source_url, date_published__range=date_range)

       clean_url = self.get_url_clean_name(source_url)

       ex = EntriesExporter(self, entries)
       ex.export_entries(source_url, clean_url, self.get_export_path_daily(day_iso))

   def get_export_path_daily(self, day_iso):
       day_path = Path(day_iso)
       entries_dir = self.get_export_path() / day_iso
       return entries_dir

   def write_all_files_for_day_joined_separate(self, day_iso):
       """ We do not want to provide for each day cumulative view. Users may want to select which 'streams' are selected individually '"""
       from .models import RssSourceDataModel, RssSourceEntryDataModel

       date_range = DateUtils.get_range4day(day_iso)

       # some entries might not have source in the database - added manually.
       # first capture entries, then check if has export to CMS.
       # if entry does not have source, it was added manually and is subject for export

       entries = RssSourceEntryDataModel.objects.filter(date_published__range = date_range)
       sources_urls = set(entries.values_list('source', flat=True).distinct())

       for source_url in sources_urls:
           source_objs = RssSourceDataModel.objects.filter(url = source_url)
           if source_objs.exists() and not source_objs[0].export_to_cms:
              continue

           self.write_files_for_source_for_day(source_url, day_iso)

   def write_files_favourite(self):
       from .exporters.highlightsexporter import HighlightsBigExporter

       exporter = HighlightsBigExporter(self)
       exporter.export()

   def write_sources(self):
       from .models import RssSourceDataModel
       from .converters import SourcesConverter

       sources = RssSourceDataModel.objects.filter(export_to_cms = True)
       converter = SourcesConverter()
       converter.set_sources(sources)
       converter.export(self)

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

   def t_refresh(self, item):
       log = logging.getLogger(self.app_name)

       PersistentInfo.create("Refreshing RSS data")

       from .models import RssSourceDataModel
       sources = RssSourceDataModel.objects.all()
       for source in sources:
           self.download_rss(source)

       from .gitupdatemgr import GitUpdateManager

       git_mgr = GitUpdateManager(self)
       git_mgr.check_if_git_update()

       #self.fix_tags()

   def fix_tags(self):
       PersistentInfo.create("Fixing tags")
       from .models import RssEntryTagsDataModel, RssSourceEntryDataModel
       tags = RssEntryTagsDataModel.objects.all()
       for tag in tags:
            if tag.link_obj == None:
                links = RssSourceEntryDataModel.objects.filter(link = tag.link)
                if links.exists():
                     tag.link_obj = links[0]
                     tag.save()
       PersistentInfo.create("Fixing tags done")

   def get_bookmarks_path(self):
       return self.get_export_path() / "bookmarks"

   def get_url_clean_name(self, file_name):
       file_name = file_name.replace(":", ".")\
              .replace("/", "")\
              .replace("\\","")\
              .replace("?",".")\
              .replace("=",".")

       return file_name
