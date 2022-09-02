from pathlib import Path

from .threads import *
from .basictypes import *

__version__ = "0.0.1"


class Configuration(object):
   obj = None

   def __init__(self):
       self.directory = Path(".").resolve()
       self.links_directory = self.directory / "link_files"
       self.version = __version__
       self.server_log_file = self.directory / "server_log_file.txt"

       self.enable_logging()
       self.create_threads()

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
       file_name = file_name.replace(":", "").replace("/", "").replace("\\","")
       path = Path(".")
       rss_path = path / 'rss'
       if not rss_path.exists():
           rss_path.mkdir()
       
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

                   from dateutil import parser
                   date = parser.parse(entry.published)
                   date = date.isoformat()

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


   def download_rss(self, item):
       self.threads[0].add_to_process_list(item)

   def t_refresh(self, item):
      logging.info("Refreshing: ")

      from .models import RssLinkDataModel
      sources = RssLinkDataModel.objects.all()
      for source in sources:
          self.download_rss(source)

