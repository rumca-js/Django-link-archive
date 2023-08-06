"""
@brief This file provides handlers for 'jobs'.
"""
import logging
import traceback
from datetime import date, datetime
from pathlib import Path

from django.db.models import Q

from .apps import LinkDatabase
from .models import (
    PersistentInfo,
    ConfigurationEntry,
    BackgroundJob,
)
from .models import RssSourceExportHistory
from .pluginsources.sourcecontrollerbuilder import SourceControllerBuilder
from .basictypes import fix_path_for_windows
from .programwrappers import ytdlp, id3v2
from .controllers import (
    BackgroundJobController,
    LinkDataController,
    SourceDataController,
)
from .configuration import Configuration


class BaseJobHandler(object):
    """!
    Base handler
    """

    def get_job_filter(self):
        return Q(job=self.get_job())

    def set_config(self, config):
        self._config = config

    def get_files_with_extension(self, input_path, extension):
        result = []
        for root, dirs, files in os.walk(path):
            for afile in files:
                if afile.endswith(extension):
                    result.append(os.path.join(root, afile))
        return result


class ProcessSourceJobHandler(BaseJobHandler):
    """!
    Processes source, checks if contains new entries
    """

    def __init__(self):
        pass

    def get_job(self):
        return BackgroundJob.JOB_PROCESS_SOURCE

    def process(self, obj=None):
        try:
            sources = SourceDataController.objects.filter(url=obj.subject)
            if len(sources) == 0:
                return

            source = sources[0]

            plugin = SourceControllerBuilder.get(source)
            plugin.check_for_data()

        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception during parsing page contents {0} {1} {2}".format(
                    source.url, str(e), error_text
                )
            )


class LinkDownloadJobHandler(BaseJobHandler):
    """!
    downloads entry
    """

    def __init__(self):
        pass

    def get_job(self):
        return BackgroundJob.JOB_LINK_DOWNLOAD

    def process(self, obj=None):
        try:
            item = LinkDataController.objects.filter(link=obj.subject)[0]
            from .webtools import Page

            p = Page(item.link)
            p.download_all()
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception downloading web page {0} {1} {2}".format(
                    obj.subject, str(e), error_text
                )
            )


class LinkMusicDownloadJobHandler(BaseJobHandler):
    """!
    downloads entry music
    """

    def __init__(self):
        pass

    def get_job(self):
        return BackgroundJob.JOB_LINK_DOWNLOAD_MUSIC

    def process(self, obj=None):
        try:
            item = LinkDataController.objects.filter(link=obj.subject)[0]

            PersistentInfo.create("Downloading music: " + item.link + " " + item.title)
            # TODO pass dir?

            file_name = Path(str(item.artist)) / str(item.album) / item.title
            file_name = str(file_name) + ".mp3"
            file_name = fix_path_for_windows(file_name)

            yt = ytdlp.YTDLP(item.link)
            if not yt.download_audio(file_name):
                PersistentInfo.error(
                    "Could not download music: " + item.link + " " + item.title
                )
                return

            data = {"artist": item.artist, "album": item.album, "title": item.title}

            id3 = id3v2.Id3v2(file_name, data)
            id3.tag()
            PersistentInfo.create(
                "Downloading music done: " + item.link + " " + item.title
            )
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception downloading music {0} {1} {2}".format(
                    obj.subject, str(e), error_text
                )
            )


class LinkVideoDownloadJobHandler(BaseJobHandler):
    """!
    downloads entry video
    """

    def __init__(self):
        pass

    def get_job(self):
        return BackgroundJob.JOB_LINK_DOWNLOAD_VIDEO

    def process(self, obj=None):
        try:
            item = LinkDataController.objects.filter(link=obj.subject)[0]

            PersistentInfo.create("Downloading video: " + item.link + " " + item.title)

            yt = ytdlp.YTDLP(item.link)
            if not yt.download_video("file.mp4"):
                PersistentInfo.error(
                    "Could not download video: " + item.link + " " + item.title
                )
                return

            PersistentInfo.create(
                "Downloading video done: " + item.link + " " + item.title
            )
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception downloading video {0} {1} {2}".format(
                    obj.subject, str(e), error_text
                )
            )


class LinkAddJobHandler(BaseJobHandler):
    """!
    Adds entry to database
    """

    def __init__(self):
        pass

    def get_job(self):
        return BackgroundJob.JOB_LINK_ADD

    def process(self, obj=None):
        try:
            link = obj.subject
            source_id = obj.args
            source_obj = SourceDataController.objects.get(id=int(source_id))
            data = {"user": None, "language": source_obj.language, "persistent": False}

            print("Adding {} for {}".format(link, source_obj.title))
            try:
                LinkDataController.create_from_youtube(link, data)
            except Exception as e:
                try:
                    LinkDataController.create_from_youtube(link, data)
                except Exception as e:
                    error_text = traceback.format_exc()
                    PersistentInfo.error(
                        "Exception on adding link {} {}".format(str(e), error_text)
                    )
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception downloading video {0} {1} {2}".format(
                    obj.subject, str(e), error_text
                )
            )


class LinkArchiveJobHandler(BaseJobHandler):
    """!
    Archives entry to database
    """

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
            PersistentInfo.error(
                "Exception on LinkArchiveHandler {} {}".format(str(e), error_text)
            )


class WriteDailyDataJobHandler(BaseJobHandler):
    """!
    Writes daily data to disk
    """

    def __init__(self):
        pass

    def get_job(self):
        return BackgroundJob.JOB_WRITE_DAILY_DATA

    def process(self, obj=None):
        try:
            from .datawriter import DataWriter

            # some changes could be done externally. Through apache.
            from django.core.cache import cache

            cache.clear()

            writer = DataWriter(self._config)

            date_input = datetime.strptime(obj.subject, "%Y-%m-%d").date()

            writer.write_daily_data(date_input.isoformat())
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception: Yearly generation: {} {}".format(str(e), error_text)
            )


class ImportDailyDataJobHandler(BaseJobHandler):
    """!
    Writes daily data to disk
    """

    def __init__(self):
        pass

    def get_job(self):
        return BackgroundJob.JOB_IMPORT_DAILY_DATA

    def process(self, obj=None):
        c = Configuration.get_object()

        import_path = c.get_import_path()

        valid_dirs = []
        dirs = os.listdir(import_path)
        for adir in dirs:
            if adir != "bookmarks":
                valid_dirs.append(import_path / adir)

        for avalid_dir in valid_dirs:
            files = self.get_files_with_extension(avalid_dir, "json")
            for afile in files:
                self.import_one_file(afile)

    def import_one_file(self, afile):
        import json

        with open(import_file) as json_file:
            data = json.load(json_file)

            for json_entry in data:
                export_names = LinkDataController.get_export_names()

                create_args = {}
                for export_name in export_names:
                    create_args[export_name] = json_source[export_name]

                LinkDataController.objects.create(create_args)

                # TODO import tags also


class ImportBookmarksJobHandler(BaseJobHandler):
    """!
    Writes daily data to disk
    """

    def __init__(self):
        pass

    def get_job(self):
        return BackgroundJob.JOB_IMPORT_BOOKMARKS

    def process(self, obj=None):
        c = Configuration.get_object()
        import_path = c.get_import_path() / "bookmarks"

        files = self.get_files_with_extension(import_path, "json")
        for afile in files:
            self.import_one_file(afile)

    def import_one_file(self, afile):
        import json

        with open(import_file) as json_file:
            data = json.load(json_file)

            for json_entry in data:
                export_names = LinkDataController.get_export_names()

                create_args = {}
                for export_name in export_names:
                    create_args[export_name] = json_source[export_name]

                LinkDataController.objects.create(create_args)

                # TODO import tags also


class ImportSourcesJobHandler(BaseJobHandler):
    """!
    Writes daily data to disk
    """

    def __init__(self):
        pass

    def get_job(self):
        return BackgroundJob.JOB_IMPORT_SOURCES

    def process(self, obj=None):
        import json

        c = Configuration.get_object()
        import_file = c.get_import_path() / "sources.json"

        with open(import_file) as json_file:
            data = json.load(json_file)

            for json_source in data:
                export_names = SourceDataController.get_export_names()

                create_args = {}
                for export_name in export_names:
                    create_args[export_name] = json_source[export_name]

                SourceDataController.objects.create(**create_args)


class WriteBookmarksJobHandler(BaseJobHandler):
    """!
    Writes bookmarks data to disk
    """

    def __init__(self):
        pass

    def get_job(self):
        return BackgroundJob.JOB_WRITE_BOOKMARKS

    def process(self, obj=None):
        try:
            from .configuration import Configuration
            from .datawriter import DataWriter

            # some changes could be done externally. Through apache.
            from django.core.cache import cache

            cache.clear()

            c = Configuration.get_object()
            writer = DataWriter(c)
            writer.write_bookmarks()
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception: Writing bookmarks: {} {}".format(str(e), error_text)
            )


class WriteTopicJobHandler(BaseJobHandler):
    """!
    Writes topic data to disk
    """

    def __init__(self):
        pass

    def get_job(self):
        return BackgroundJob.JOB_WRITE_TOPIC_DATA

    def process(self, obj=None):
        try:
            from ..serializers.bookmarksexporter import BookmarksTopicExporter

            # some changes could be done externally. Through apache.
            from django.core.cache import cache

            cache.clear()

            topic = obj.subject

            c = Configuration.get_object()
            exporter = BookmarksTopicExporter(c)
            exporter.export(topic)
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception: Writing topic data: {} {}".format(str(e), error_text)
            )


class PushToRepoJobHandler(BaseJobHandler):
    """!
    Pushes data to repo
    """

    def __init__(self):
        pass

    def get_job(self):
        return BackgroundJob.JOB_PUSH_TO_REPO

    def process(self, obj=None):
        try:
            if (
                ConfigurationEntry.get().is_bookmark_repo_set()
                and ConfigurationEntry.get().is_daily_repo_set()
            ):
                from .gitupdatemgr import GitUpdateManager

                git_mgr = GitUpdateManager(self._config)
                git_mgr.write_and_push_to_git()

                yesterday = DateUtils.get_date_yesterday()
                new_history = RssSourceExportHistory(date=yesterday)
                new_history.save()
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error("Exception: {} {}".format(str(e), error_text))


class PushDailyDataToRepoJobHandler(BaseJobHandler):
    """!
    Pushes data to repo
    """

    def __init__(self):
        pass

    def get_job(self):
        return BackgroundJob.JOB_PUSH_DAILY_DATA_TO_REPO

    def process(self, obj=None):
        try:
            if ConfigurationEntry.get().is_daily_repo_set():
                from .gitupdatemgr import GitUpdateManager

                date_input = obj.subject

                git_mgr = GitUpdateManager(self._config)
                git_mgr.write_and_push_daily_data(date_input)
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error("Exception: {} {}".format(str(e), error_text))


class RefreshThreadHandler(object):
    """!
    refreshes sources, synchronously
    """

    def __init__(self, name="RefreshThreadHandler"):
        pass

    def refresh(self, item=None):
        PersistentInfo.create("Refreshing RSS data")

        from .controllers import SourceDataController

        sources = SourceDataController.objects.all()
        for source in sources:
            BackgroundJobController.download_rss(source)

        conf = ConfigurationEntry.get()

        if RssSourceExportHistory.is_update_required():
            if conf.is_bookmark_repo_set() or conf.is_daily_repo_set():
                BackgroundJobController.push_to_repo()

                if ConfigurationEntry.get().source_archive:
                    sources = SourceDataController.objects.all()
                    for source in sources:
                        BackgroundJobController.link_archive(source.url)

            LinkDataController.clear_old_entries()
            LinkDataController.move_old_links_to_archive()


class HandlerManager(object):
    """!
    Threading manager
    """

    def __init__(self):
        pass

    def get_handlers(self):
        return [
            PushToRepoJobHandler(),
            PushDailyDataToRepoJobHandler(),
            ProcessSourceJobHandler(),
            LinkAddJobHandler(),
            LinkDownloadJobHandler(),
            LinkMusicDownloadJobHandler(),
            LinkVideoDownloadJobHandler(),
            LinkArchiveJobHandler(),
            WriteDailyDataJobHandler(),
            WriteBookmarksJobHandler(),
            WriteTopicJobHandler(),
            ImportSourcesJobHandler(),
            ImportBookmarksJobHandler(),
            ImportDailyDataJobHandler(),
        ]

    def get_handler_and_object(self):
        afilter = None
        for key, handler in enumerate(self.get_handlers()):
            afilter = handler.get_job_filter()

            objs = BackgroundJob.objects.filter(afilter)
            if len(objs) != 0:
                obj = objs[0]
                return [obj, handler]
        return []

    def process_all(self):
        from .configuration import Configuration

        config = Configuration.get_object()

        while True:
            items = self.get_handler_and_object()
            if len(items) == 0:
                break
            else:
                obj = items[0]
                handler = items[1]

                handler.set_config(config)

                handler.process(obj)
                obj.delete()
