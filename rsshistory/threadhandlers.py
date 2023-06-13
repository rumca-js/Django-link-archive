import logging
import traceback
from datetime import date, datetime, timedelta
from pathlib import Path

from django.db.models import Q

from .views import app_name
from .models import LinkDataModel, SourceDataModel, PersistentInfo, ConfigurationEntry, BackgroundJob
from .models import RssSourceImportHistory, RssSourceExportHistory
from .threads import *
from .pluginsources.basepluginbuilder import BasePluginBuilder
from .basictypes import fix_path_for_windows
from .programwrappers import ytdlp,id3v2


class ProcessSourceHandler(ThreadJobCommon):

    def __init__(self, name="ProcessSourceHandler", seconds_wait=10, itemless=False):
        ThreadJobCommon.__init__(self, name, seconds_wait, itemless)

    def set_parent(self, parent):
        self.parent = parent

    def get_process_item(self):
        objs = BackgroundJob.objects.filter(job=BackgroundJob.JOB_PROCESS_SOURCE)
        if len(objs) == 0:
            return None

        obj = objs[0]
        sources = SourceDataModel.objects.filter(url = obj.subject)
        obj.delete()

        if len(sources) != 0:
            source = sources[0]
            return source

    def process_item(self, source=None):
        try:
           plugin = BasePluginBuilder.get(source)
           plugin.check_for_data()

           if len(RssSourceImportHistory.objects.filter(url = source.url, date = date.today())) == 0:
               history = RssSourceImportHistory(url = source.url, date = date.today(), source_obj = source)
               history.save()
        except Exception as e:
           error_text = traceback.format_exc()
           PersistentInfo.error("Exception during parsing page contents {0} {1} {2}".format(source.url, str(e), error_text))


class DownloadLinkHandler(ThreadJobCommon):

    def __init__(self, name="DownloadMusicHandler", seconds_wait=10, itemless=False):
        ThreadJobCommon.__init__(self, name, seconds_wait, itemless)

    def set_parent(self, parent):
        self.parent = parent

    def get_process_item(self):
        criterion1 = Q(job=BackgroundJob.JOB_LINK_DOWNLOAD)
        criterion2 = Q(job=BackgroundJob.JOB_LINK_DOWNLOAD_MUSIC)
        criterion3 = Q(job=BackgroundJob.JOB_LINK_DOWNLOAD_VIDEO)
        criterion4 = Q(job=BackgroundJob.JOB_LINK_ADD)

        objs = BackgroundJob.objects.filter(criterion1 | criterion2 | criterion3 | criterion4)
        if len(objs) == 0:
            return None

        obj = objs[0]
        return obj

    def process_item(self, item=None):
        try:
            if item.job == BackgroundJob.JOB_LINK_DOWNLOAD_MUSIC:
                self.process_music_item(item)
            elif item.job == BackgroundJob.JOB_LINK_DOWNLOAD_VIDEO:
                self.process_video_item(item)
            elif item.job == BackgroundJob.JOB_LINK_DOWNLOAD:
                self.process_link_item(item)
            elif item.job == BackgroundJob.JOB_LINK_ADD:
                self.process_link_add(item)
            else:
                raise NotImplemented("Not supported process error")

        except Exception as e:
           error_text = traceback.format_exc()
           PersistentInfo.error("Exception on LinkArchiveHandler {} {}".format(str(e), error_text))

        item.delete()

    def process_link_add(self, obj=None):
       link = obj.subject
       source_id = obj.args
       source_obj = SourceDataModel.objects.get(id = int(source_id))
       data = {"user" : None, "language" : source_obj.language, "persistent" : False}

       print("Adding {} for {}".format(link, source_obj.title))
       try:
           LinkDataModel.create_from_youtube(link, data)
       except Exception as e:
           try:
               LinkDataModel.create_from_youtube(link, data)
           except Exception as e:
               error_text = traceback.format_exc()
               PersistentInfo.error("Exception on adding link {} {}".format(str(e), error_text))

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
            BackgroundJob.download_rss(source)

        if ConfigurationEntry.get().is_git_set():
            if RssSourceExportHistory.is_update_required():
               BackgroundJob.push_to_repo()

               if ConfigurationEntry.get().source_archive:
                   from .models import SourceDataModel
                   sources = SourceDataModel.objects.all()
                   for source in sources:
                       BackgroundJob.link_archive(source.url)


class LinkArchiveHandler(ThreadJobCommon):
    def __init__(self, name="LinkArchiveHandler", seconds_wait=10, itemless=False):
        ThreadJobCommon.__init__(self, name, seconds_wait, itemless)

    def set_parent(self, parent):
        self.parent = parent

    def get_process_item(self):
        objs = BackgroundJob.objects.filter(job=BackgroundJob.JOB_LINK_ARCHIVE)
        if len(objs) == 0:
            return None

        obj = objs[0]
        item = obj.subject
        obj.delete()

        return item

    def process_item(self, item=None):
        try:
            from .services.waybackmachine import WaybackMachine
            wb = WaybackMachine()
            if wb.is_saved(item):
                wb.save(item)

            objs = BackgroundJob.objects.filter(job=BackgroundJob.JOB_LINK_ARCHIVE, subject = item)
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

        criterion1 = Q(job=BackgroundJob.JOB_WRITE_DAILY_DATA)
        criterion2 = Q(job=BackgroundJob.JOB_WRITE_TOPIC_DATA)
        criterion3 = Q(job=BackgroundJob.JOB_WRITE_BOOKMARKS)

        objs = BackgroundJob.objects.filter(criterion1 | criterion2 | criterion3)
        if len(objs) == 0:
            return None

        obj = objs[0]
        return obj

    def process_item(self, item=None):
        try:
            if item.job == BackgroundJob.JOB_WRITE_DAILY_DATA:
                self.write_daily_data(item)
            elif item.job == BackgroundJob.JOB_WRITE_TOPIC_DATA:
                self.write_topic_data(item)
            elif item.job == BackgroundJob.JOB_WRITE_BOOKMARKS:
                self.write_bookmarks(item)
            else:
                raise NotImplemented("Not supported process error")

            item.delete()
        except Exception as e:
           error_text = traceback.format_exc()
           PersistentInfo.error("Exception on LinkArchiveHandler {} {}".format(str(e), error_text))

    def write_daily_data(self, obj=None):
        try:
            from .datawriter import DataWriter
            writer = DataWriter(self._config)

            date_input = datetime.strptime(obj.subject, '%Y-%m-%d').date()

            writer.write_daily_data(date_input.isoformat())
        except Exception as e:
           error_text = traceback.format_exc()
           PersistentInfo.error("Exception: Yearly generation: {} {}".format(str(e), error_text))

    def write_topic_data(self, obj=None):
        try:
            from ..serializers.bookmarksexporter import BookmarksTopicExporter

            topic = obj.subject

            c = Configuration.get_object(str(app_name))
            exporter = BookmarksTopicExporter(c)
            exporter.export(topic)
        except Exception as e:
           error_text = traceback.format_exc()
           PersistentInfo.error("Exception: Writing topic data: {} {}".format(str(e), error_text))

    def write_bookmarks(self, obj=None):
        try:
            from .prjconfig import Configuration
            from .datawriter import DataWriter
            
            c = Configuration.get_object(str(app_name))
            writer = DataWriter(c)
            writer.write_bookmarks()
        except Exception as e:
           error_text = traceback.format_exc()
           PersistentInfo.error("Exception: Writing bookmarks: {} {}".format(str(e), error_text))


class RepoThreadHandler(ThreadJobCommon):
    def __init__(self, name="RepoThreadHandler", seconds_wait=10, itemless=False):
        ThreadJobCommon.__init__(self, name, seconds_wait, itemless)

    def set_parent(self, parent):
        self.parent = parent

    def get_process_item(self):
        objs = BackgroundJob.objects.filter(job=BackgroundJob.JOB_PUSH_TO_REPO)
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

       BackgroundJob.truncate_invalid_jobs()

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

   def download_music(self, item):
       bj = BackgroundJob.download_music(item.link)
       return True

   def download_video(self, item):
       bj = BackgroundJob.download_video(item.link)
       return True

   def wayback_save(self, url):
       bj = BackgroundJob.link_archive(url)
       return True

   def youtube_details(self, url):
       bj = BackgroundJob.youtube_details(url)
       return True

   def write_daily_data(self, input_date):
       bj = BackgroundJob.write_daily_data(input_date)
       return True
