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
from .programwrappers import ytdlp, id3v2


class BaseJobHandler(object):
    def get_job_filter(self):
        return Q(job=self.get_job())

    def set_config(self, config):
        self._config = config


class ProcessSourceJobHandler(BaseJobHandler):

    def __init__(self):
        pass

    def get_job(self):
        return BackgroundJob.JOB_PROCESS_SOURCE

    def process(self, obj=None):
        try:
            sources = SourceDataModel.objects.filter(url=obj.subject)
            if len(sources) == 0:
                return

            source = sources[0]

            plugin = BasePluginBuilder.get(source)
            plugin.check_for_data()

            if len(RssSourceImportHistory.objects.filter(url=source.url, date=date.today())) == 0:
                history = RssSourceImportHistory(url=source.url, date=date.today(), source_obj=source)
                history.save()
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception during parsing page contents {0} {1} {2}".format(source.url, str(e), error_text))


class LinkDownloadJobHandler(BaseJobHandler):
    def __init__(self):
        pass

    def get_job(self):
        return BackgroundJob.JOB_LINK_DOWNLOAD

    def process(self, obj=None):
        try:
            item = LinkDataModel.objects.filter(link=obj.subject)[0]
            from .webtools import Page
            p = Page(item.link)
            p.download_all()
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error("Exception downloading web page {0} {1} {2}".format(obj.subject, str(e), error_text))


class LinkMusicDownloadJobHandler(BaseJobHandler):
    def __init__(self):
        pass

    def get_job(self):
        return BackgroundJob.JOB_LINK_DOWNLOAD_MUSIC

    def process(self, obj=None):
        try:
            item = LinkDataModel.objects.filter(link=obj.subject)[0]

            PersistentInfo.create("Downloading music: " + item.link + " " + item.title)
            # TODO pass dir?

            file_name = Path(str(item.artist)) / str(item.album) / item.title
            file_name = str(file_name) + ".mp3"
            file_name = fix_path_for_windows(file_name)

            yt = ytdlp.YTDLP(item.link)
            if not yt.download_audio(file_name):
                PersistentInfo.error("Could not download music: " + item.link + " " + item.title)
                return

            data = {'artist': item.artist, 'album': item.album, 'title': item.title}

            id3 = id3v2.Id3v2(file_name, data)
            id3.tag()
            PersistentInfo.create("Downloading music done: " + item.link + " " + item.title)
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error("Exception downloading music {0} {1} {2}".format(obj.subject, str(e), error_text))


class LinkVideoDownloadJobHandler(BaseJobHandler):
    def __init__(self):
        pass

    def get_job(self):
        return BackgroundJob.JOB_LINK_DOWNLOAD_VIDEO

    def process(self, obj=None):
        try:
            item = LinkDataModel.objects.filter(link=obj.subject)[0]

            PersistentInfo.create("Downloading video: " + item.link + " " + item.title)

            yt = ytdlp.YTDLP(item.link)
            if not yt.download_video('file.mp4'):
                PersistentInfo.error("Could not download video: " + item.link + " " + item.title)
                return

            PersistentInfo.create("Downloading video done: " + item.link + " " + item.title)
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error("Exception downloading video {0} {1} {2}".format(obj.subject, str(e), error_text))


class LinkAddJobHandler(BaseJobHandler):
    def __init__(self):
        pass

    def get_job(self):
        return BackgroundJob.JOB_LINK_ADD

    def process(self, obj=None):
        try:
            link = obj.subject
            source_id = obj.args
            source_obj = SourceDataModel.objects.get(id=int(source_id))
            data = {"user": None, "language": source_obj.language, "persistent": False}

            print("Adding {} for {}".format(link, source_obj.title))
            try:
                LinkDataModel.create_from_youtube(link, data)
            except Exception as e:
                try:
                    LinkDataModel.create_from_youtube(link, data)
                except Exception as e:
                    error_text = traceback.format_exc()
                    PersistentInfo.error("Exception on adding link {} {}".format(str(e), error_text))
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error("Exception downloading video {0} {1} {2}".format(obj.subject, str(e), error_text))


class LinkArchiveJobHandler(BaseJobHandler):
    def __init__(self):
        pass

    def get_job(self):
        return BackgroundJob.JOB_LINK_ARCHIVE

    def process(self, obj=None):
        try:
            item = obj.subject

            from .services.waybackmachine import WaybackMachine
            wb = WaybackMachine()
            if wb.is_saved(item):
                wb.save(item)
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error("Exception on LinkArchiveHandler {} {}".format(str(e), error_text))


class WriteDailyDataJobHandler(BaseJobHandler):
    def __init__(self):
        pass

    def get_job(self):
        return BackgroundJob.JOB_WRITE_DAILY_DATA

    def process(self, obj=None):
        try:
            from .datawriter import DataWriter
            writer = DataWriter(self._config)

            date_input = datetime.strptime(obj.subject, '%Y-%m-%d').date()

            writer.write_daily_data(date_input.isoformat())
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error("Exception: Yearly generation: {} {}".format(str(e), error_text))


class WriteBookmarksJobHandler(BaseJobHandler):
    def __init__(self):
        pass

    def get_job(self):
        return BackgroundJob.JOB_WRITE_BOOKMARKS

    def process(self, obj=None):
        try:
            from .prjconfig import Configuration
            from .datawriter import DataWriter

            c = Configuration.get_object(str(app_name))
            writer = DataWriter(c)
            writer.write_bookmarks()
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error("Exception: Writing bookmarks: {} {}".format(str(e), error_text))


class WriteTopicJobHandler(BaseJobHandler):
    def __init__(self):
        pass

    def get_job(self):
        return BackgroundJob.JOB_WRITE_TOPIC_DATA

    def process(self, obj=None):
        try:
            from ..serializers.bookmarksexporter import BookmarksTopicExporter

            topic = obj.subject

            c = Configuration.get_object(str(app_name))
            exporter = BookmarksTopicExporter(c)
            exporter.export(topic)
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error("Exception: Writing topic data: {} {}".format(str(e), error_text))


class PushToRepoJobHandler(BaseJobHandler):
    def __init__(self):
        pass

    def get_job(self):
        return BackgroundJob.JOB_PUSH_TO_REPO

    def process(self, obj=None):
        try:
            if ConfigurationEntry.get().is_git_set():
                from .gitupdatemgr import GitUpdateManager

                git_mgr = GitUpdateManager(self._config)
                git_mgr.write_and_push_to_git()
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error("Exception: {} {}".format(str(e), error_text))


class MultiJobHandler(ThreadJobCommon):

    def __init__(self, name="MultiJobHandler", handlers=[]):
        seconds_wait = 10
        itemless = False
        self.handlers = handlers
        ThreadJobCommon.__init__(self, name, seconds_wait, itemless)

    def set_config(self, config):
        self._cfg = config
        for key, handler in enumerate(self.handlers):
            handler.set_config(self._cfg)

    def get_process_item(self):
        afilter = None
        for key, handler in enumerate(self.handlers):
            afilter = handler.get_job_filter()

            objs = BackgroundJob.objects.filter(afilter)
            if len(objs) != 0:
                obj = objs[0]
                return obj

    def process_item(self, item=None):
        try:
            processed = False
            for key, handler in enumerate(self.handlers):
                if item.job == handler.get_job():
                    handler.process(item)
                    processed = True
                    break

            if not processed:
                raise NotImplemented("Not supported process error")

        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error("Exception on LinkArchiveHandler {} {}".format(str(e), error_text))

        if item:
            item.delete()


class RefreshThreadHandler(ThreadJobCommon):

    def __init__(self, name="RefreshThreadHandler"):
        itemless = True
        seconds_wait = 900
        ThreadJobCommon.__init__(self, name, seconds_wait, itemless)

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


class HandlerManager(object):

    def __init__(self, config):
        self._cfg = config
        self.create_threads()

    def create_threads(self):
        refresh_seconds = 1800

        BackgroundJob.truncate_invalid_jobs()

        conf = ConfigurationEntry.get()
        refresh_seconds = conf.sources_refresh_period

        refresh_thread = RefreshThreadHandler("refresh-thread")

        # proessing new RSS sources is priority, should be at the first place
        handlers = [
            PushToRepoJobHandler(),
            ProcessSourceJobHandler(),
            LinkAddJobHandler(),
            LinkDownloadJobHandler(),
            LinkMusicDownloadJobHandler(),
            LinkVideoDownloadJobHandler(),
            LinkArchiveJobHandler(),
            WriteDailyDataJobHandler(),
            WriteBookmarksJobHandler(),
            WriteTopicJobHandler(),
        ]
        jobs_thread = MultiJobHandler("jobs-thread", handlers)

        self.threads = [
            refresh_thread,
            jobs_thread,
        ]

        for athread in self.threads:
            athread.set_config(self._cfg)
            athread.start()

    def close(self):
        for athread in self.threads:
            athread.close()
