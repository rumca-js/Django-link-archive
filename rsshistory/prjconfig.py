from pathlib import Path
import time
import shutil
import logging
from datetime import datetime
from datetime import timedelta
from pytz import timezone

from .gitrepo import *

from .threads import *
from .basictypes import *
from .models import ConfigurationEntry

__version__ = "0.1.3"


class Configuration(object):
   obj = None

   def __init__(self, app_name):
       self.app_name = str(app_name)

       self.directory = Path("/home/rumpel/WorkDir/DjangoPage/linklibrary")
       self.version = __version__
       self.server_log_file = self.directory / "log_{0}.txt".format(app_name)

       self.enable_logging()
       self.create_threads()

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

   def get_data_path(self):
       return self.directory / 'data' / self.app_name

   def get_rss_tmp_path(self):
       rss_path = self.get_export_path() / 'downloaded_rss'
       if not rss_path.exists():
           rss_path.mkdir()
       return rss_path

   def export_entries(self, entries, export_type = "default", entries_dir = None, with_description = True):
       from .models import EntriesConverter

       if len(entries) == 0:
           return

       e_converter = EntriesConverter()
       e_converter.set_entries(entries)
       e_converter.with_description = with_description

       if entries_dir is None:
           entries_dir = self.get_export_path() / self.get_date_file_name()
       else:
           entries_dir = self.get_export_path() / entries_dir

       export_path = entries_dir

       if not export_path.exists():
           export_path.mkdir()

       file_name = export_path / (export_type + "_entries.json")
       file_name.write_text(e_converter.get_text())

       file_name = export_path / (export_type + "_entries.md")
       file_name.write_bytes(e_converter.get_md_text().encode("utf-8", "ingnore"))

   def create_threads(self):
       download_rss = ThreadJobCommon("download-rss")
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
      if thread == "download-rss":
          try:
             self.t_download_rss(item)
             self.write_files_today(item)
          except Exception as e:
             log = logging.getLogger(self.app_name)
             log.error("Exception during parsing page contents {0}".format(item.source) )
             log.critical(e, exc_info=True)
      elif thread == "refresh-thread":
         self.t_refresh(item)

         log = logging.getLogger(self.app_name)
         log.info("Writing favourites")
         self.write_files_favourite()
      else:
         raise NotImplemented

   def t_download_rss(self, item):
       try:
           import feedparser
           log = logging.getLogger(self.app_name)

           url = item.url

           file_name = url + ".txt"
           file_name = self.get_url_clean_name(file_name)

           queue_size = self.threads[0].get_queue_size()

           # log.info("Source: {0} {1}; Queue: {2}".format(item.url, item.title, queue_size))

           start_time = datetime.datetime.now(timezone('UTC'))

           if item.date_fetched:
               time_since_update = start_time - item.date_fetched
               mins = time_since_update / timedelta(minutes = 1)

               if mins < 10:
                   # log.info("Source: {0} {1} Skipped; Queue: {2}".format(item.url, item.title, queue_size))
                   return

           #rss_contents = self.get_page(url)
           #
           #if rss_contents:
           #    feed = feedparser.parse(rss_contents)
           #    rss_path = self.get_rss_tmp_path()
           #    file_path = rss_path / file_name
           #    file_path.write_bytes(rss_contents)
           #else:
           feed = feedparser.parse(url)

           if len(feed.entries) == 0:
               log.error("Source: {0} {1} Has no data; Queue: {2}".format(item.url, item.title, queue_size))
           else:
               for entry in feed.entries:
                   self.process_rss_entry(item, entry)

           stop_time = datetime.datetime.now(timezone('UTC'))
           total_time = stop_time - start_time
           total_time.total_seconds() 

           item.date_fetched = stop_time
           item.save()

       except Exception as e:
          log = logging.getLogger(self.app_name)
          queue_size = self.threads[0].get_queue_size()
          log.error("Source: {0} {1} NOK; Queue: {2}".format(item.url, item.title, queue_size))
          log.critical(e, exc_info=True)

   def process_rss_entry(self, item, entry):
       try:
          from .models import RssSourceEntryDataModel
          objs = RssSourceEntryDataModel.objects.filter(link = entry.link)

          if not objs.exists():
              if str(entry.title).strip() == "" or entry.title == "undefined":
                  return False

              if entry.link.find("TVN24-po-ukrainsku") >= 0:
                  return False

              description = ""
              if hasattr(entry, "description"):
                  description = entry.description

              published = ""
              o = None
              
              if hasattr(entry, "published"):

                  date = self.get_date_iso(entry.published)

                  o = RssSourceEntryDataModel(
                      source = item.url,
                      title = entry.title,
                      description = description,
                      link = entry.link,
                      date_published = date)
              else:
                  log = logging.getLogger(self.app_name)
                  log.error("RSS link does not have 'published' keyword {0}".format(item.url))

                  o = RssSourceEntryDataModel(
                      source = item.url,
                      title = entry.title,
                      description = description,
                      link = entry.link)

              if o:
                  o.save()

              return True

       except Exception as e:
          log = logging.getLogger(self.app_name)
          queue_size = self.threads[0].get_queue_size()
          log.error("Entry: {0} {1} NOK/Queue: {2}".format(item.url, item.title, queue_size))
          log.critical(e, exc_info=True)

          return False

   def write_files_today(self, item):
       if not item.export_to_cms:
           return

       from .models import RssSourceEntryDataModel

       date_range = self.get_datetime_range_one_day()
       entries = RssSourceEntryDataModel.objects.filter(source = item.url, date_published__range=date_range)
       self.export_entries(entries, self.get_url_clean_name(item.url))

   def write_files_favourite(self):
       from .models import RssSourceEntryDataModel

       entries = RssSourceEntryDataModel.objects.filter(favourite = True)
       self.export_entries(entries, "favourite", "favourite", False)

   def download_rss(self, item):
       self.threads[0].add_to_process_list(item)

   def t_refresh(self, item):
       log = logging.getLogger(self.app_name)

       log.info("Refreshing RSS data")

       from .models import RssSourceDataModel
       sources = RssSourceDataModel.objects.all()
       for source in sources:
           self.download_rss(source)

       try:
           ob = ConfigurationEntry.objects.all()
           if ob.exists() and ob[0].is_git_set():
               conf = ob[0]
               repo = GitRepo(conf)

               day_changed = self.is_day_changed(repo.get_local_dir() )
               month_changed = self.is_month_changed(repo.get_local_dir() )

               if day_changed:
                      self.push_to_git(conf)

               if day_changed:
                   pass
                   # TODO clear description of non-favourite up to 500 chars
               if month_changed:
                   pass
                   # TODO clear description of non-favourite

       except Exception as e:
          log = logging.getLogger(self.app_name)
          log.error("Exception during refresh")
          log.critical(e, exc_info=True)

   def is_day_changed(self, local_dir):
       yesterday = self.get_yesterday()
       expected_dir = local_dir / self.get_year(yesterday) / self.get_month(yesterday) / self.format_date(yesterday)

       if expected_dir.is_dir():
           return False

       return True

   def is_month_changed(self, local_dir):
       yesterday = self.get_yesterday()
       expected_dir = local_dir / self.get_year(yesterday) / self.get_month(yesterday)

       if expected_dir.is_dir():
           return False

       return True

   def push_to_git(self, conf):
       log = logging.getLogger(self.app_name)
       log.info("Pushing to RSS link repo")

       repo = GitRepo(conf)

       repo.up()

       self.copy_yesterday(repo)
       self.copy_favourites(repo)
       
       yesterday = self.get_yesterday()

       repo.add([])
       repo.commit(self.format_date(yesterday))
       repo.push()

   def copy_yesterday(self, repo):
       yesterday = self.get_yesterday()
       local_dir = self.get_export_path() / self.format_date(yesterday)
       expected_dir = repo.get_local_dir() / self.get_year(yesterday) / self.get_month(yesterday) / self.format_date(yesterday)

       shutil.copytree(local_dir, expected_dir)

   def copy_favourites(self, repo):
       local_dir = self.get_export_path() / "favourite"
       expected_dir = repo.get_local_dir()

       shutil.copytree(local_dir, expected_dir, dirs_exist_ok=True)

   def get_datetime_file_name(self):
       return datetime.datetime.today().strftime('%Y-%m-%d_%H-%M-%S')

   def get_date_file_name(self):
       return self.format_date(datetime.datetime.today())

   def format_date(self, date):
       return date.strftime('%Y-%m-%d')

   def get_url_clean_name(self, file_name):
       file_name = file_name.replace(":", "").replace("/", "").replace("\\","")
       return file_name

   def get_date_iso(self, timestamp):
      from dateutil import parser
      date = parser.parse(timestamp)
      date = date.isoformat()
      return date

   def get_year(self, datetime):
       return datetime.strftime('%Y')

   def get_month(self, datetime):
       return datetime.strftime('%m')

   def get_yesterday(self):
      from datetime import date, timedelta

      current_date = date.today()
      prev_day = current_date - timedelta(days = 1) 

      return prev_day

   def get_tommorow(self):
      from datetime import date, timedelta

      current_date = date.today()
      next_day = current_date + timedelta(days = 1)

      return next_day

   def get_datetime_range_one_day(self):
      from datetime import date, timedelta

      current_date = date.today()
      next_day = self.get_tommorow()

      return (current_date, next_day)

   def get_page(self, url):
       import urllib.request, urllib.error, urllib.parse
       try:
           req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

           data = None
           with urllib.request.urlopen(req) as response:
               data = response.read()
               # webContent = response.decode('UTF-8')
           return data
       except Exception as e:
          log = logging.getLogger(self.app_name)
          log.error("Exception during parsing page contents")
          log.critical(e, exc_info=True)
