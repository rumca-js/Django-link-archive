from datetime import date, datetime, timedelta
import logging
import traceback
from pathlib import Path

from .threads import *
from .sources.rsssourceprocessor import RssSourceProcessor
from .programwrappers import ytdlp,id3v2
from .datawriter import *
from .models import LinkDataModel, SourceDataModel, PersistentInfo, ConfigurationEntry, BackgroundJob
from .models import RssSourceImportHistory
from .basictypes import fix_path_for_windows


class ProcessSourceHandler(ThreadJobCommon):

    def __init__(self, name="ProcessSourceHandler", seconds_wait=10, itemless=False):
        ThreadJobCommon.__init__(self, name, seconds_wait, itemless)

    def set_parent(self, parent):
        self.parent = parent

    def get_process_item(self):
        objs = BackgroundJob.objects.filter(job="process-source")
        if len(objs) == 0:
            return None

        obj = objs[0]
        items = SourceDataModel.objects.filter(url = obj.subject)
        obj.delete()

        if len(items) != 0:
            item = items[0]
        return item

    def process_item(self, item=None):
        try:
           proc = RssSourceProcessor(self._config)
           proc.process_source(item)

           if len(RssSourceImportHistory.objects.filter(url = item.url, date = date.today())) == 0:
               history = RssSourceImportHistory(url = item.url, date = date.today(), source_obj = item)
               history.save()

           if ConfigurationEntry.objects.all()[0].is_git_set():
               today = DateUtils.get_iso_today()
               if item.export_to_cms:
                   writer = SourceEntriesDataWriter(self._config, item.url)
                   writer.write_for_day(today)
        except Exception as e:
           error_text = traceback.format_exc()
           PersistentInfo.error("Exception during parsing page contents {0} {1} {2}".format(item.url, str(e), error_text))


class DownloadMusicHandler(ThreadJobCommon):

    def __init__(self, name="DownloadMusicHandler", seconds_wait=10, itemless=False):
        ThreadJobCommon.__init__(self, name, seconds_wait, itemless)

    def set_parent(self, parent):
        self.parent = parent

    def get_process_item(self):
        objs = BackgroundJob.objects.filter(job="download-music")
        if len(objs) == 0:
            return None

        obj = objs[0]
        items = LinkDataModel.objects.filter(link = obj.subject)
        obj.delete()

        if len(items) != 0:
            item = items[0]
            return item

    def process_item(self, item=None):
      log = logging.getLogger(self._config.app_name)
      PersistentInfo.create("Downloading music: " + item.link + " " + item.title)
      # TODO pass dir?

      file_name = Path(str(item.artist)) / str(item.album) / item.title
      file_name = str(file_name) + ".mp3"
      file_name = fix_path_for_windows(file_name)

      yt = ytdlp.YTDLP(item.link)
      if not yt.download_audio(file_name):
          PersistentInfo.error("Could not download music: " + item.link + " " + item.title)
          return

      data = {'artist' : item.artist, 'album' : item.album, 'title' : item.title }

      id3 = id3v2.Id3v2(file_name, data)
      id3.tag()
      PersistentInfo.create("Downloading music done: " + item.link + " " + item.title)

      objs = BackgroundJob.objects.filter(job="download-music", subject = item.link)
      objs.delete()


class DownloadVideoHandler(ThreadJobCommon):

    def __init__(self, name="DownloadVideoHandler", seconds_wait=10, itemless=False):
        ThreadJobCommon.__init__(self, name, seconds_wait, itemless)

    def set_parent(self, parent):
        self.parent = parent

    def get_process_item(self):
        objs = BackgroundJob.objects.filter(job="download-video")
        if len(objs) == 0:
            return None

        obj = objs[0]
        items = LinkDataModel.objects.filter(link = obj.subject)
        obj.delete()

        if len(items) != 0:
            item = items[0]
            return item

    def process_item(self, item=None):
      log = logging.getLogger(self._config.app_name)

      PersistentInfo.create("Downloading video: " + item.link + " " + item.title)

      yt = ytdlp.YTDLP(item.link)
      if not yt.download_video('file.mp4'):
          PersistentInfo.error("Could not download video: " + item.link + " " + item.title)
          return

      PersistentInfo.create("Downloading video done: " + item.link + " " + item.title)

      objs = BackgroundJob.objects.filter(job="download-video", subject = item.link)
      objs.delete()


class RefreshThreadHandler(ThreadJobCommon):

    def __init__(self, name="RefreshThreadHandler", seconds_wait=10, itemless=True):
        ThreadJobCommon.__init__(self, name, seconds_wait, itemless)

    def set_parent(self, parent):
        self.parent = parent

    def get_process_item(self):
        pass

    def process_item(self, item=None):
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
            self.parent.download_rss(source)

        if ConfigurationEntry.objects.all()[0].is_git_set():
            from .gitupdatemgr import GitUpdateManager

            git_mgr = GitUpdateManager(self._config)
            git_mgr.check_if_git_update()


class WaybackSaveHandler(ThreadJobCommon):
    def __init__(self, name="WaybackSaveHandler", seconds_wait=10, itemless=False):
        ThreadJobCommon.__init__(self, name, seconds_wait, itemless)

    def set_parent(self, parent):
        self.parent = parent

    def get_process_item(self):
        objs = BackgroundJob.objects.filter(job="link-save")
        if len(objs) == 0:
            return None

        obj = objs[0]
        item = obj.subject
        obj.delete()

        return item

    def process_item(self, item=None):
        try:
            from .sources.waybackmachine import WaybackMachine
            wb = WaybackMachine()
            if wb.is_saved(item):
                wb.save(item)

            objs = BackgroundJob.objects.filter(job="link-save", subject = item)
            objs.delete()
        except Exception as e:
           error_text = traceback.format_exc()
           PersistentInfo.error("Exception on WaybackSaveHandler {} {}".format(str(e), error_text))


class YouTubeDetailsHandler(ThreadJobCommon):
    def __init__(self, name="YouTubeDetailsHandler", seconds_wait=10, itemless=False):
        ThreadJobCommon.__init__(self, name, seconds_wait, itemless)

    def set_parent(self, parent):
        self.parent = parent

    def get_process_item(self):
        objs = BackgroundJob.objects.filter(job="link-refresh")
        if len(objs) == 0:
            return None

        obj = objs[0]
        items = LinkDataModel.objects.filter(link = obj.subject)
        obj.delete()

        if len(items) != 0:
            item = items[0]
            return item

    def process_item(self, item=None):
        pass


class YearlyGeneration(ThreadJobCommon):
    def __init__(self, name="YearlyGeneration", seconds_wait=10, itemless=False):
        ThreadJobCommon.__init__(self, name, seconds_wait, itemless)

    def set_parent(self, parent):
        self.parent = parent

    def get_process_item(self):
        objs = BackgroundJob.objects.filter(job="write-yearly-data")
        if len(objs) == 0:
            return None
        obj = objs[0]
        return obj

    def process_item(self, year=None):
        try:
            start = '2022-01-01'
            stop = '2022-12-31'

            date_start = datetime.strptime(start, '%Y-%m-%d').date()
            date_stop = datetime.strptime(stop, '%Y-%m-%d').date()
            if date_stop < date_start:
                PersistentInfo.error("Yearly generation: Incorrect configuration of dates start:{} stop:{}".format(date_start, date_stop))

            from .datawriter import DataWriter
            writer = DataWriter(self._config)

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

   def create_threads(self):
       refresh_seconds = 3600

       BackgroundJob.truncate()

       from .models import ConfigurationEntry
       confs = ConfigurationEntry.objects.all()
       if len(confs) > 0:
           refresh_seconds = confs[0].sources_refresh_period

       process_source = ProcessSourceHandler("process-source")
       download_music = DownloadMusicHandler("download-music")
       download_video = DownloadVideoHandler("download-video")
       refresh_thread = RefreshThreadHandler("refresh-thread", refresh_seconds, True)
       wayback_save = WaybackSaveHandler("link-save")
       yt_details = YouTubeDetailsHandler("link-refresh")
       yearly = YearlyGeneration("write-yearly-data")

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
           athread.set_config(self._cfg)
           athread.set_parent(self)
           athread.start()

   def close(self):
       for athread in self.threads:
           athread.close()

   def download_rss(self, item, force = False):
       if force == False:
           if item.is_fetch_possible() == False:
               return False

       bj = BackgroundJob.objects.create(job="process-source", task=None, subject=item.url, args="")
       return True

   def download_music(self, item):
       bj = BackgroundJob.objects.create(job="download-music", task=None, subject=item.link, args="")
       return True

   def download_video(self, item):
       bj = BackgroundJob.objects.create(job="download-video", task=None, subject=item.link, args="")
       return True

   def wayback_save(self, url):
       bj = BackgroundJob.objects.create(job="link-save", task=None, subject=url, args="")
       return True

   def youtube_details(self, url):
       bj = BackgroundJob.objects.create(job="link-details", task=None, subject=url, args="")
       return True

   def write_yearly_data(self, year):
       bj = BackgroundJob.objects.create(job="write-yearly-data", task=None, subject=url, args="")
       return True
