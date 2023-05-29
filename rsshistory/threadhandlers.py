from datetime import date, datetime, timedelta
import logging
import traceback

from .threads import *
from .sources.rsssourceprocessor import RssSourceProcessor
from .programwrappers import ytdlp,id3v2
from .datawriter import *
from .models import PersistentInfo, ConfigurationEntry, RssSourceImportHistory
from .basictypes import fix_path_for_windows


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

           if ConfigurationEntry.objects.all()[0].is_git_set():
               today = DateUtils.get_iso_today()
               if not item.export_to_cms:
                  return

               writer = SourceEntriesDataWriter(self._cfg, item.url)
               writer.write_for_day(today)
        except Exception as e:
           error_text = traceback.format_exc()
           PersistentInfo.error("Exception during parsing page contents {0} {1} {2}".format(item.url, str(e), error_text))


class DownloadMusicHandler(object):
    def __init__(self, thread_parent):
        self._cfg = thread_parent._cfg
        self.thread_parent = thread_parent

    def process(self, item):
      log = logging.getLogger(self._cfg.app_name)
      PersistentInfo.create("Downloading music: " + item.url + " " + item.title)
      # TODO pass dir?

      file_name = Path(item.artist) / item.album / item.title
      file_name = str(file_name) + ".mp3"
      file_name = fix_path_for_windows(file_name)

      yt = ytdlp.YTDLP(item.url)
      if not yt.download_audio(file_name):
          PersistentInfo.error("Could not download music: " + item.url + " " + item.title)
          return

      data = {'artist' : item.artist, 'album' : item.album, 'title' : item.title }

      id3 = id3v2.Id3v2(file_name, data)
      id3.tag()
      PersistentInfo.create("Downloading music done: " + item.url + " " + item.title)


class DownloadVideoHandler(object):
    def __init__(self, thread_parent):
        self._cfg = thread_parent._cfg
        self.thread_parent = thread_parent

    def process(self, item):
      log = logging.getLogger(self._cfg.app_name)

      PersistentInfo.create("Downloading video: " + item.url + " " + item.title)

      yt = ytdlp.YTDLP(item.url)
      if not yt.download_video('file.mp4'):
          PersistentInfo.error("Could not download video: " + item.url + " " + item.title)
          return

      PersistentInfo.create("Downloading video done: " + item.url + " " + item.title)


class RefreshThreadHandler(object):
    def __init__(self, thread_parent):
        self._cfg = thread_parent._cfg
        self.thread_parent = thread_parent

    def process(self, item):
        try:
            self.t_refresh(item)
        except Exception as e:
           error_text = traceback.format_exc()
           PersistentInfo.error("Exception during parsing page contents {0} {1} {2}".format(item.url, str(e), error_text))

    def t_refresh(self, item):
        PersistentInfo.create("Refreshing RSS data")

        from .models import SourceDataModel
        sources = SourceDataModel.objects.all()
        for source in sources:
            self.thread_parent.download_rss(source)

        if ConfigurationEntry.objects.all()[0].is_git_set():
            from .gitupdatemgr import GitUpdateManager

            git_mgr = GitUpdateManager(self._cfg)
            git_mgr.check_if_git_update()


class WaybackSaveHandler(object):
    def __init__(self, thread_parent):
        self._cfg = thread_parent._cfg
        self.thread_parent = thread_parent

    def process(self, item):
        try:
            from .sources.waybackmachine import WaybackMachine
            wb = WaybackMachine()
            if wb.is_saved(item):
                wb.save(item)
        except Exception as e:
           error_text = traceback.format_exc()
           PersistentInfo.error("Exception on WaybackSaveHandler {} {}".format(str(e), error_text))


class YouTubeDetailsHandler(object):
    def __init__(self, thread_parent):
        self._cfg = thread_parent._cfg
        self.thread_parent = thread_parent

    def process(self, item):
        pass


class YearlyGeneration(object):
    def __init__(self, thread_parent):
        self._cfg = thread_parent._cfg
        self.thread_parent = thread_parent

    def process(self, year):
        try:
            start = '2022-01-01'
            stop = '2022-12-31'

            date_start = datetime.strptime(start, '%Y-%m-%d').date()
            date_stop = datetime.strptime(stop, '%Y-%m-%d').date()
            if date_stop < date_start:
                PersistentInfo.error("Yearly generation: Incorrect configuration of dates start:{} stop:{}".format(date_start, date_stop))

            from .datawriter import DataWriter
            writer = DataWriter(self._cfg)

            current_date = date_start
            while current_date <= date_stop:
                print("Generating for time: {}".format(current_date))
                writer.write_daily_data(current_date.isoformat())
                current_date += timedelta(days=1)
        except Exception as e:
           error_text = traceback.format_exc()
           PersistentInfo.error("Exception: Yearly generation: {} {}".format(str(e), error_text))


class HandlerManager(object):

   def __init__(self, config):
      self._cfg = config
      self.create_threads()

   def t_process_item(self, thread, item):
      if thread == "process-source":
          handler = ProcessSourceHandler(self)
          handler.process(item)
      elif thread == "download-music":
           handler = DownloadMusicHandler(self)
           handler.process(item)
      elif thread == "download-video":
           handler = DownloadVideoHandler(self)
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
      elif thread == "yearly-generation":
           handler = YearlyGeneration(self)
           handler.process(item)
      else:
          PersistentInfo.error("Not implemented processing thread {0}".format(thread))
          raise NotImplemented

   def create_threads(self):
       refresh_seconds = 3600

       from .models import ConfigurationEntry
       confs = ConfigurationEntry.objects.all()
       if len(confs) > 0:
           refresh_seconds = confs[0].sources_refresh_period

       process_source = ThreadJobCommon("process-source")
       download_music = ThreadJobCommon("download-music")
       download_video = ThreadJobCommon("download-video")
       refresh_thread = ThreadJobCommon("refresh-thread", refresh_seconds, True)
       wayback_save = ThreadJobCommon("wayback")
       yt_details = ThreadJobCommon("youtube-details")
       yearly = ThreadJobCommon("yearly-generation")

       self.threads = [
               process_source,
               download_music,
               download_video,
               refresh_thread,
               wayback_save,
               yt_details,
               yearly
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

   def download_music(self, item):
       self.threads[1].add_to_process_list(item)
       return True

   def download_video(self, item):
       self.threads[2].add_to_process_list(item)
       return True

   def wayback_save(self, url):
       self.threads[4].add_to_process_list(url)
       return True

   def youtube_details(self, url):
       PersistentInfo.create("Download YouTube details:{}".format(url))
       self.threads[5].add_to_process_list(url)
       return True

   def write_yearly_data(self, year):
       PersistentInfo.create("Download for year:{}".format(year))
       self.threads[6].add_to_process_list(year)
       return True
