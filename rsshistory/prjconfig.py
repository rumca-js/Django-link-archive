from pathlib import Path
import subprocess

from .threads import *
from .basictypes import *
from .models import ConfigurationEntry

__version__ = "0.0.4"


class Configuration(object):
   obj = None

   def __init__(self):
       self.directory = Path(".").resolve()
       self.links_directory = self.directory / "link_files"
       self.version = __version__
       self.server_log_file = self.directory / "server_log_file.txt"

       self.enable_logging()
       self.create_threads()

   def get_rss_tmp_path(self):
       path = Path(".")
       rss_path = path / 'exports' / 'rsshistory' / 'downloaded_rss'
       if not rss_path.exists():
           rss_path.mkdir()
       return rss_path

   def get_export_path(self):
       path = Path(".")
       rss_path = path / 'exports' / 'rsshistory'
       if not rss_path.exists():
           rss_path.mkdir()
       return rss_path

   def export_entries(self, entries, export_type = "default"):
       from .models import RssLinkDataModel, RssLinkEntryDataModel, SourcesConverter, EntriesConverter

       if len(entries) == 0:
           return

       e_converter = EntriesConverter()
       e_converter.set_entries(entries)

       export_path = self.get_export_path() / self.get_date_file_name()

       if not export_path.exists():
           export_path.mkdir()

       file_name = export_path / (export_type + "_entries.json")
       file_name.write_text(e_converter.get_text())

       #file_name = export_path / (export_type + "_entries.csv")
       #file_name.write_text(e_converter.get_csv_text())

       file_name = export_path / (export_type + "_entries.txt")
       file_name.write_text(e_converter.get_clean_text())

   def get_object():
       if not Configuration.obj:
           Configuration.obj = Configuration()
       return Configuration.obj

   def enable_logging(self):
       logging.shutdown()

       self.server_log_file.unlink(True)

       logging.basicConfig(level=logging.INFO, filename=self.server_log_file)

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

   def close(self):
       for athread in self.threads:
           athread.close()

   def t_process_item(self, thread, item):
      if thread == "download-rss":
         self.t_download_rss(item)
      elif thread == "refresh-thread":
         self.t_refresh(item)
      else:
         raise NotImplemented

   def t_download_rss(self, item):
       from .models import RssLinkEntryDataModel
       import feedparser

       url = item.url
       feed = feedparser.parse(url)

       file_name = url + ".txt"
       file_name = self.get_url_clean_name(file_name)
       rss_path = self.get_rss_tmp_path()
       
       file_path = rss_path / file_name
       file_path.write_text(str(feed))

       print(item.url + " " + item.title)

       #print(feed.feed)
       #print(feed.entries)
       #print(feed.feed.title)
       #print(feed.feed.subtitle)

       #objs = RssLinkEntryDataModel.objects.filter(url = 'http://www.e-polityka.pl/rss/rss.php?d=36')
       #if objs.exists():
       #    objs.delete()
       #objs = RssLinkEntryDataModel.objects.filter(title = 'undefined')
       #if objs.exists():
       #    objs.delete()
       #objs = RssLinkEntryDataModel.objects.filter(url = 'http://www.e-polityka.pl/rss/rss.php?d=37')
       #if objs.exists():
       #    objs.delete()
       #objs = RssLinkEntryDataModel.objects.filter(url = 'https://joemonster.org/backend.php')
       #if objs.exists():
       #    objs.delete()
       #objs = RssLinkEntryDataModel.objects.filter(url = 'https://joemonster.org/backend.php')
       #if objs.exists():
       #    objs.delete()

       #objs = RssLinkEntryDataModel.objects.all()
       #if objs.exists():
       #    for obj in objs:
       #        if obj.link.find("TVN24-po-ukrainsku") >= 0:
       #            obj.delete()

       objs = RssLinkEntryDataModel.objects.all()
       if objs.exists():
           for obj in objs:
               if str(obj.title).strip == "":
                   obj.delete()

       for entry in feed.entries:

           objs = RssLinkEntryDataModel.objects.filter(link = entry.link)

           if not objs.exists():
               if str(entry.title).strip() == "" or entry.title == "undefined":
                   continue

               if entry.link.find("TVN24-po-ukrainsku") >= 0:
                   continue

               description = ""

               #print(entry.title)
               #print()

               if hasattr(entry, "description"):
                   # print(entry.description)
                   # no more than 500 chars
                   description = entry.description[:500]

               published = ""
               if hasattr(entry, "published"):

                   date = self.get_date_iso(entry.published)

                   o = RssLinkEntryDataModel(
                       url = item.url,
                       title = entry.title,
                       description = description,
                       link = entry.link,
                       date_published = date)
               else:
                   # print(entry)

                   o = RssLinkEntryDataModel(
                       url = item.url,
                       title = entry.title,
                       description = description,
                       link = entry.link)

               o.save()
           #else:
           #    print("Entry already exists")

       date_range = self.get_datetime_range_one_day()
       entries = RssLinkEntryDataModel.objects.filter(url = item.url, date_published__range=date_range)
       self.export_entries(entries, self.get_url_clean_name(item.url))

   def download_rss(self, item):
       self.threads[0].add_to_process_list(item)

   def t_refresh(self, item):
      logging.info("Refreshing: ")

      from .models import RssLinkDataModel
      sources = RssLinkDataModel.objects.all()
      for source in sources:
          self.download_rss(source)

      ob = ConfigurationEntry.objects.all()
      if ob.exists():
         self.push_to_git(ob[0])

   def push_to_git(self, conf):
       git_path = Path(conf.git_path)
       if not git_path.exists():
          git_path.mkdir(parents=True, exist_ok = False)
          subprocess.run(["git", "clone", conf.git_repo], cwd=git_path)

   def get_datetime_file_name(self):
       return datetime.datetime.today().strftime('%Y-%m-%d_%H-%M-%S')

   def get_date_file_name(self):
       return datetime.datetime.today().strftime('%Y-%m-%d')

   def get_url_clean_name(self, file_name):
       file_name = file_name.replace(":", "").replace("/", "").replace("\\","")
       return file_name

   def get_date_iso(self, timestamp):
      from dateutil import parser
      date = parser.parse(timestamp)
      date = date.isoformat()
      return date

   def get_datetime_range_one_day(self):
      from datetime import date, timedelta

      current_date = date.today()
      next_day = current_date + timedelta(days = 1) 

      return (current_date, next_day)
