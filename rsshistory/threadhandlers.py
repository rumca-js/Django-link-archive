from datetime import date, datetime, timedelta
import logging
import traceback
from pathlib import Path

from .threads import *
from .sources.rsssourceprocessor import RssSourceProcessor
from .programwrappers import ytdlp,id3v2
from .datawriter import *
from .models import LinkDataModel, SourceDataModel, PersistentInfo, ConfigurationEntry, BackgroundJob
from .models import RssSourceImportHistory, RssSourceExportHistory
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

           #if ConfigurationEntry.get().is_git_set():
           #    today = DateUtils.get_iso_today()
           #    if item.export_to_cms:
           #        writer = SourceEntriesDataWriter(self._config, item.url)
           #        writer.write_for_day(today)
        except Exception as e:
           error_text = traceback.format_exc()
           PersistentInfo.error("Exception during parsing page contents {0} {1} {2}".format(item.url, str(e), error_text))


class DownloadLinkHandler(ThreadJobCommon):

    def __init__(self, name="DownloadMusicHandler", seconds_wait=10, itemless=False):
        ThreadJobCommon.__init__(self, name, seconds_wait, itemless)

    def set_parent(self, parent):
        self.parent = parent

    def get_process_item(self):
        from django.db.models import Q
        criterion1 = Q(job="download-music")
        criterion2 = Q(job="download-video")
        criterion3 = Q(job="link-download")

        objs = BackgroundJob.objects.filter(criterion1 | criterion2 | criterion3)
        if len(objs) == 0:
            return None

        obj = objs[0]
        return obj

    def process_item(self, item=None):
        try:
            if item.job == "download-music":
                self.process_music_item(item)
            elif item.job == "download-video":
                self.process_video_item(item)
            elif item.job == "link-download":
                self.process_link_item(item)
            else:
                raise NotImplemented("Not supported process error")

            item.delete()
        except Exception as e:
           error_text = traceback.format_exc()
           PersistentInfo.error("Exception on LinkArchiveHandler {} {}".format(str(e), error_text))

    def process_music_item(self, obj=None):
      item = LinkDataModel.objects.filter(link = obj.subject)[0]

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

    def process_video_item(self, obj=None):
      item = LinkDataModel.objects.filter(link = obj.subject)[0]

      PersistentInfo.create("Downloading video: " + item.link + " " + item.title)

      yt = ytdlp.YTDLP(item.link)
      if not yt.download_video('file.mp4'):
          PersistentInfo.error("Could not download video: " + item.link + " " + item.title)
          return

      PersistentInfo.create("Downloading video done: " + item.link + " " + item.title)

    def process_link_item(self, obj=None):
      item = LinkDataModel.objects.filter(link = obj.subject)[0]
      from .webtools import Page
      p = Page(item.link)
      p.download_all()


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
           PersistentInfo.error("Exception during parsing page contents {0} {1} {2}".format(item, str(e), error_text))

    def t_refresh(self, item):
        PersistentInfo.create("Refreshing RSS data")

        from .models import SourceDataModel
        sources = SourceDataModel.objects.all()
        for source in sources:
           if source.is_fetch_possible() == False:
               continue

           if len(BackgroundJob.objects.filter(job="process-source", subject=source.url)) == 0: 
               BackgroundJob.objects.create(job="process-source", task=None, subject=source.url, args="")

        if ConfigurationEntry.get().is_git_set():
            if RssSourceExportHistory.is_update_required():
               BackgroundJob.objects.create(job="push-to-repo", task=None, subject="", args="")

               if ConfigurationEntry.get().source_archive:
                   from .models import SourceDataModel
                   sources = SourceDataModel.objects.all()
                   for source in sources:
                       BackgroundJob.objects.create(job="link-archive", task=None, subject=source.url, args="")


class LinkArchiveHandler(ThreadJobCommon):
    def __init__(self, name="LinkArchiveHandler", seconds_wait=10, itemless=False):
        ThreadJobCommon.__init__(self, name, seconds_wait, itemless)

    def set_parent(self, parent):
        self.parent = parent

    def get_process_item(self):
        objs = BackgroundJob.objects.filter(job="link-archive")
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

            objs = BackgroundJob.objects.filter(job="link-archive", subject = item)
            objs.delete()
        except Exception as e:
           error_text = traceback.format_exc()
           PersistentInfo.error("Exception on LinkArchiveHandler {} {}".format(str(e), error_text))


class WriteThreadHandler(ThreadJobCommon):
    def __init__(self, name="WriteThreadHandler", seconds_wait=10, itemless=False):
        ThreadJobCommon.__init__(self, name, seconds_wait, itemless)

    def set_parent(self, parent):
        self.parent = parent

    def get_process_item(self):
        objs = BackgroundJob.objects.filter(job="write-yearly-data")
        if len(objs) == 0:
            return None
        obj = objs[0]
        return obj

    def process_item(self, obj=None):
        try:
            from .datawriter import DataWriter
            writer = DataWriter(self._config)

            date_input = datetime.strptime(obj.subject, '%Y-%m-%d').date()

            print("Generating for time: {}".format(date_input))
            writer.write_daily_data(date_input.isoformat())
        except Exception as e:
           error_text = traceback.format_exc()
           PersistentInfo.error("Exception: Yearly generation: {} {}".format(str(e), error_text))

    def write_multiple_items(self, start='2022-01-01', stop = '2022-12-31'):
        try:
            date_start = datetime.strptime(start, '%Y-%m-%d').date()
            date_stop = datetime.strptime(stop, '%Y-%m-%d').date()
            if date_stop < date_start:
                PersistentInfo.error("Yearly generation: Incorrect configuration of dates start:{} stop:{}".format(date_start, date_stop))

            current_date = date_start
            while current_date <= date_stop:
                print("Generating for time: {}".format(current_date))
                str_date = current_date.isoformat()

                BackgroundJob.objects.create(job='write-yearly-data', task=None, subject=str_date, args="")
        except Exception as e:
           error_text = traceback.format_exc()
           PersistentInfo.error("Exception: Yearly generation: {} {}".format(str(e), error_text))


class RepoThreadHandler(ThreadJobCommon):
    def __init__(self, name="RepoThreadHandler", seconds_wait=10, itemless=False):
        ThreadJobCommon.__init__(self, name, seconds_wait, itemless)

    def set_parent(self, parent):
        self.parent = parent

    def get_process_item(self):
        objs = BackgroundJob.objects.filter(job="push-to-repo")
        if len(objs) == 0:
            return None
        obj = objs[0]
        return obj

    def process_item(self, obj=None):
        if obj == None:
            return	
        try:
            if ConfigurationEntry.get().is_git_set():
                from .gitupdatemgr import GitUpdateManager

                git_mgr = GitUpdateManager(self._config)
                git_mgr.write_and_push_to_git()
                
            obj.delete()
        except Exception as e:
           error_text = traceback.format_exc()
           PersistentInfo.error("Exception: {} {}".format(str(e), error_text))


class HandlerManager(object):

   def __init__(self, config):
      self._cfg = config
      self.create_threads()

   def create_threads(self):
       refresh_seconds = 1800

       BackgroundJob.truncate()

       conf = ConfigurationEntry.get()
       refresh_seconds = conf.sources_refresh_period

       process_source = ProcessSourceHandler("process-source")
       download_thread = DownloadLinkHandler("download")
       refresh_thread = RefreshThreadHandler("refresh-thread", refresh_seconds, True)
       # sometimes it takes long to archive links
       link_archive = LinkArchiveHandler("link-archive")
       write_thread = WriteThreadHandler("write-thread")
       repo_thread = RepoThreadHandler("repo-thread")

       self.threads = [
               process_source,
               download_thread,
               refresh_thread,
               link_archive,
               write_thread,
               repo_thread
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
       bj = BackgroundJob.objects.create(job="link-archive", task=None, subject=url, args="")
       return True

   def youtube_details(self, url):
       bj = BackgroundJob.objects.create(job="link-details", task=None, subject=url, args="")
       return True

   def write_yearly_data(self, year):
       bj = BackgroundJob.objects.create(job="write-yearly-data", task=None, subject=year, args="")
       return True
