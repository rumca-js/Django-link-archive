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
from .models import ConfigurationEntry
from .dateutils import DateUtils
from .prjgitrepo import *
from .models import PersistentInfo, RssSourceExportHistory, RssSourceImportHistory
from .sources.basepluginbuilder import BasePluginBuilder


__version__ = "0.4.1"


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

       self.threads = [
               download_rss,
               refresh_thread
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

      if item:
          PersistentInfo.text("thread {0} item {1}".format(thread, item.url))
      else:
          PersistentInfo.text("thread {0}".format(thread))

      if thread == "process-source":
          try:
             proc = RssSourceProcessor(self)
             proc.process_source(item)

             if len(RssSourceImportHistory.objects.filter(date = date.today())) == 0:
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

       ex = EntriesExporter(self, entries)
       path = Path(day_iso)
       ex.export_entries(source_url, self.get_url_clean_name(source_url), path)

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

       sources = RssSourceDataModel.objects.all()
       converter = SourcesConverter()
       converter.set_sources(sources)
       converter.export(self)

   def download_rss(self, item, force = False):
       if force == False:
           if item.is_fetch_possible() == False:
               return False

       PersistentInfo.text("Adding item to list: {0} {1}".format(item.url, item.title))
       self.threads[0].add_to_process_list(item)
       return True

   def check_if_git_update(self):
       try:
           yesterday = DateUtils.get_date_yesterday()

           history = RssSourceExportHistory.objects.filter(date = yesterday)

           ob = ConfigurationEntry.objects.all()
           if ob.exists() and ob[0].is_git_set():
               conf = ob[0]
               repo = DailyRepo(conf, conf.git_daily_repo)

               day_present = repo.is_day_data_present(yesterday)
               month_changed = DateUtils.is_month_changed()

               if not day_present:
                   PersistentInfo.create("Day has changed, pushing data to git")
                   self.write_all_files_for_day_joined_separate(yesterday.isoformat())
                   self.write_files_favourite()
                   #self.write_all_files_for_day_joined()
                   self.write_sources()

                   self.push_to_git(conf)
                   PersistentInfo.create("Data successfully pushed to git")

                   if len(RssSourceExportHistory.objects.filter(date = date.today())) == 0:
                       history = RssSourceExportHistory(date = date.today())
                       history.save()

               if not day_present:
                   self.clear_old_entries()
                   pass
                   # TODO clear description of non-favourite up to 500 chars

       except Exception as e:
          log = logging.getLogger(self.app_name)
          error_text = traceback.format_exc()
          PersistentInfo.error("Exception during refresh: {0} {1}".format(str(e), error_text))
          log.critical(e, exc_info=True)

   def t_refresh(self, item):
       log = logging.getLogger(self.app_name)

       PersistentInfo.create("Refreshing RSS data")

       from .models import RssSourceDataModel
       sources = RssSourceDataModel.objects.all()
       for source in sources:
           self.download_rss(source)

       self.clear_old_entries()

       self.check_if_git_update()

       #from .sources.waybackmachine import WaybackMachine
       #wb = WaybackMachine()
       #wb.get_wayback_at_time("www.google.com", "2022")

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

   def debug_refresh(self):
       days = [
               #'2022-09-05',
               #'2022-09-06',
               #'2022-09-07',
               #'2022-09-08',
               #'2022-09-09',
               #'2022-09-10',
               #'2022-09-11',
               #'2022-09-12',
               #'2022-09-13',
               #'2022-09-14',
               #'2022-09-15',
               #'2022-09-16',
               #'2022-09-17',
               #'2022-09-18',
               #'2022-09-19',
               #'2022-09-20',
               #'2022-09-21',
               #'2022-09-22',
               #'2022-09-23',
               #'2022-09-24',
               #'2022-09-25',
               #'2022-09-26',
               #'2022-09-27',
               #'2022-09-28',
               #'2022-09-29',
               #'2022-09-30',
               #'2022-10-01',
               #'2022-10-02',
               #'2022-10-03',
               #'2022-10-04',
               #'2022-10-05',
               #'2022-10-06',
               #'2022-10-07',
               #'2022-10-08',
               #'2022-10-09',
               #'2022-10-10',
               #'2022-10-11',
               #'2022-10-12',
               #'2022-10-13',
               #'2022-10-14',
               #'2022-10-15',
               #'2022-10-16',
               #'2022-10-17',
               #'2022-10-18',
               #'2022-10-19',
               #'2022-10-20',
               #'2022-10-21',
               #'2022-10-22',
               #'2022-10-23',
               #'2022-10-24',
               #'2022-10-25',
               #'2022-10-26',
               #'2022-10-27',
               #'2022-10-28',
               #'2022-10-29',
               #'2022-10-30',
               #'2022-10-31',
               #'2022-11-01',
               #'2022-11-02',
               #'2022-11-03',
               #'2022-11-04',
               #'2022-11-05',
               #'2022-11-06',
               #'2022-11-07',
               #'2022-11-08',
               #'2022-11-09',
               #'2022-11-10',
               #'2022-11-11',
               #'2022-11-12',
               #'2022-11-13',
               #'2022-11-14',
               #'2022-11-15',
               #'2022-11-16',
               #'2022-11-17',
               #'2022-11-18',
               #'2022-11-19',
               #'2022-11-20',
               #'2022-11-21',
               #'2022-11-22',
               #'2022-11-23',
               #'2022-11-24',
               #'2022-11-25',
               #'2022-11-26',
               #'2022-11-27',
               #'2022-11-28',
               #'2022-11-29',
               #'2022-11-30',
               #'2022-12-01',
               #'2022-12-02',
               #'2022-12-03',
               #'2022-12-04',
               #'2022-12-05',
               #'2022-12-06',
               #'2022-12-07',
               #'2022-12-08',
               #'2022-12-09',
               #'2022-12-10',
               #'2022-12-11',
               #'2022-12-12',
               #'2022-12-13',
               #'2022-12-14',
               '2022-12-15',
               '2022-12-16',
               '2022-12-17',
               '2022-12-18',
               '2022-12-19',
               '2022-12-20'
               ]

       for day in days:
           print("Doing for a day: {0}".format(day))
           self.write_all_files_for_day_joined_separate(day)

   def clear_old_entries(self):
       log = logging.getLogger(self.app_name)

       from .models import RssSourceDataModel, RssSourceEntryDataModel
       #sources = RssSourceDataModel.objects.filter(remove_after_days)
       sources = RssSourceDataModel.objects.all()
       for source in sources:

           if not source.is_removeable():
               continue

           days = source.get_days_to_remove()
           if days > 0:
               current_time = DateUtils.get_datetime_now_utc()
               days_before = current_time - timedelta(days = days)
               
               entries = RssSourceEntryDataModel.objects.filter(source=source.url, persistent=False, date_published__lt=days_before)
               if entries.exists():
                   PersistentInfo.create("Removing old RSS data for source: {0} {1}".format(source.url, source.title))
                   entries.delete()

   def push_to_git(self, conf):
       self.push_daily_repo(conf)
       self.push_bookmarks_repo(conf)

   def push_daily_repo(self, conf):
       log = logging.getLogger(self.app_name)
       PersistentInfo.create("Pushing to RSS link repo")
       
       yesterday = DateUtils.get_date_yesterday()

       repo = DailyRepo(conf, conf.git_daily_repo)

       repo.up()

       local_dir = self.get_export_path() / DateUtils.get_dir4date(yesterday)
       repo.copy_day_data(local_dir, yesterday)
       repo.copy_file(self.get_bookmarks_path() / "sources.json")
       
       repo.add([])
       repo.commit(DateUtils.get_dir4date(yesterday))
       repo.push()

   def push_bookmarks_repo(self, conf):
       log = logging.getLogger(self.app_name)
       PersistentInfo.create("Pushing main repo data")
       
       yesterday = DateUtils.get_date_yesterday()

       repo = MainRepo(conf, conf.git_repo)

       repo.up()

       local_dir = self.get_bookmarks_path()
       repo.copy_main_data(local_dir)

       repo.add([])
       repo.commit(DateUtils.get_dir4date(yesterday))
       repo.push()

   def get_bookmarks_path(self):
       return self.get_export_path() / "bookmarks"

   def get_url_clean_name(self, file_name):
       file_name = file_name.replace(":", ".")\
              .replace("/", "")\
              .replace("\\","")\
              .replace("?",".")\
              .replace("=",".")

       return file_name
