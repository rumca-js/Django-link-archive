from datetime import date, timedelta
import logging
import traceback

from .threads import *

from .sources.rsssourceprocessor import RssSourceProcessor
from .datawriter import *
from .models import PersistentInfo, RssSourceImportHistory


class ProcessSourceHandler(object):
    def __init__(self, thread_parent):
        self._cfg = thread_parent._cfg
        self.thread_parent = thread_parent

    def process(self, item):
        try:
           proc = RssSourceProcessor(self._cfg)
           proc.process_source(item)

           if len(RssSourceImportHistory.objects.filter(url = item.url, date = date.today())) == 0:
               history = RssSourceImportHistory(url = item.url, date = date.today(), source_obj = item)
               history.save()

           today = DateUtils.get_iso_today()
           if not item.export_to_cms:
              return

           writer = SourceEntriesDataWriter(self._cfg, item.url)
           writer.write_for_day(today)
        except Exception as e:
           log = logging.getLogger(self._cfg.app_name)
           error_text = traceback.format_exc()
           PersistentInfo.error("Exception during parsing page contents {0} {1} {2}".format(item.url, str(e), error_text))
           log.critical(e, exc_info=True)


class RefreshThreadHandler(object):
    def __init__(self, thread_parent):
        self._cfg = thread_parent._cfg
        self.thread_parent = thread_parent

    def process(self, item):
        try:
            self.t_refresh(item)
        except Exception as e:
           log = logging.getLogger(self._cfg.app_name)
           if item:
               log.error("Exception during refreshing {0}".format(item.url) )
           log.critical(e, exc_info=True)

    def t_refresh(self, item):
        log = logging.getLogger(self._cfg.app_name)

        PersistentInfo.create("Refreshing RSS data")

        from .models import RssSourceDataModel
        sources = RssSourceDataModel.objects.all()
        for source in sources:
            self.thread_parent.download_rss(source)

        from .gitupdatemgr import GitUpdateManager

        git_mgr = GitUpdateManager(self._cfg)
        git_mgr.check_if_git_update()


class WaybackSaveHandler(object):
    def __init__(self, thread_parent):
        self._cfg = thread_parent._cfg
        self.thread_parent = thread_parent

    def process(self, item):
        from .sources.waybackmachine import WaybackMachine
        wb = WaybackMachine()
        wb.save(item)


class YouTubeDetailsHandler(object):
    def __init__(self, thread_parent):
        self._cfg = thread_parent._cfg
        self.thread_parent = thread_parent

    def process(self, item):
        pass


class HandlerManager(object):

   def __init__(self, config):
      self._cfg = config
      self.create_threads()

   def t_process_item(self, thread, item):
     from datetime import date, timedelta
     from .sources.rsssourceprocessor import RssSourceProcessor

     if thread == "process-source":
         handler = ProcessSourceHandler(self)
         handler.process(item)
     elif thread == "refresh-thread":
         handler = RefreshThreadHandler(self)
         handler.process(item)
     elif thread == "wayback":
         handler = WaybackSaveHandler(self)
         handler.process(item)
     elif thread == "youtube-details":
         handler = YouTubeDetailsHandler(self)
         handler.process(item)
     else:
        log = logging.getLogger(self._cfg.app_name)
        PersistentInfo.error("Not implemented processing thread {0}".format(thread))
        log.critical(e, exc_info=True)
        raise NotImplemented

   def create_threads(self):
       download_rss = ThreadJobCommon("process-source")
       refresh_thread = ThreadJobCommon("refresh-thread", 3600, True) #3600 is 1 hour
       wayback = ThreadJobCommon("wayback")
       yt_details = ThreadJobCommon("youtube-details")

       self.threads = [
               download_rss,
               refresh_thread,
               wayback,
               yt_details
               ]

       for athread in self.threads:
           athread.set_config(self)
           athread.start()

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


   def youtube_details(self, url):
       PersistentInfo.create("Download YouTube details:{0}".format(url))
       self.threads[3].add_to_process_list(url)
       return True
