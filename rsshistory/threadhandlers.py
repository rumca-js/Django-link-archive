"""
@brief This file provides handlers for 'jobs'.
"""
import logging
import time
import traceback
from datetime import date, datetime
from pathlib import Path

from django.db.models import Q

from .apps import LinkDatabase
from .models import (
    PersistentInfo,
    BackgroundJob,
    SourceDataModel,
    Domains,
    SourceExportHistory,
    KeyWords,
    DataExport,
)
from .pluginsources.sourcecontrollerbuilder import SourceControllerBuilder
from .basictypes import fix_path_for_windows
from .programwrappers import ytdlp, id3v2
from .controllers import (
    BackgroundJobController,
    LinkDataController,
    SourceDataController,
    LinkDataHyperController,
)
from .configuration import Configuration
from .dateutils import DateUtils


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

    def get_job(self):
        return BackgroundJob.JOB_PROCESS_SOURCE

    def process(self, obj=None):
        try:
            plugin = SourceControllerBuilder.get(obj.subject)
            plugin.check_for_data()

        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception during parsing page contents {0} {1} {2}".format(
                    source.url, str(e), error_text
                )
            )


class EntryUpdateData(BaseJobHandler):
    """!
    downloads entry
    """

    def get_job(self):
        return BackgroundJob.JOB_LINK_UPDATE_DATA

    def process(self, obj=None):
        try:
            entries = LinkDataController.objects.filter(link=obj.subject)
            if len(entries) > 0:
                entry = entries[0]
                entry.update_calculated_vote()
            else:
                PersistentInfo.error(
                    "Incorrect background job {0}".format(
                        obj.subject,
                    )
                )
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception when updating link data {0} {1} {2}".format(
                    obj.subject, str(e), error_text
                )
            )


class LinkDownloadJobHandler(BaseJobHandler):
    """!
    downloads entry
    """

    def get_job(self):
        return BackgroundJob.JOB_LINK_DOWNLOAD

    def process(self, obj=None):
        try:
            item = LinkDataController.objects.filter(link=obj.subject)[0]
            from .webtools import HtmlPage

            p = HtmlPage(item.link)
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

    def get_job(self):
        return BackgroundJob.JOB_LINK_ADD

    def process(self, obj=None):
        try:
            link = obj.subject
            source_id = obj.args
            source_obj = SourceDataController.objects.get(id=int(source_id))
            data = {"user": None, "language": source_obj.language, "bookmarked": False}

            print("Adding {} for {}".format(link, source_obj.title))
            if not LinkDataHyperController.is_link(link):
                LinkDataHyperController.create_from_youtube(link, data)

        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception when adding YouTube link {0} {1} {2}".format(
                    obj.subject, str(e), error_text
                )
            )


class LinkSaveJobHandler(BaseJobHandler):
    """!
    Archives entry to database
    """

    def get_job(self):
        return BackgroundJob.JOB_LINK_SAVE

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


class ImportInstanceJobHandler(BaseJobHandler):
    """!
    Imports from instance
    """

    def get_job(self):
        return BackgroundJob.JOB_IMPORT_INSTANCE

    def process(self, obj=None):
        import json

        json_url = obj.subject

        from .serializers.instanceimporter import InstanceImporter

        ie = InstanceImporter(json_url)
        ie.import_all()


class WriteBookmarksJobHandler(BaseJobHandler):
    """!
    Writes bookmarks data to disk
    """

    def get_job(self):
        return BackgroundJob.JOB_WRITE_BOOKMARKS

    def process(self, obj=None):
        try:
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

    def get_job(self):
        return BackgroundJob.JOB_PUSH_TO_REPO

    def process(self, obj=None):
        try:
            if (
                DataExport.is_daily_data_set()
                or DataExport.is_year_data_set()
                or DataExport.is_notime_data_set()
            ):
                from .updatemgr import UpdateManager

                update_mgr = UpdateManager(self._config)
                if DataExport.is_year_data_set():
                    update_mgr.write_and_push_year_data()
                if DataExport.is_daily_data_set():
                    update_mgr.write_and_push_daily_data()
                if DataExport.is_notime_data_set():
                    update_mgr.write_and_push_notime_data()

                SourceExportHistory.confirm()
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error("Exception: {} {}".format(str(e), error_text))


class PushYearDataToRepoJobHandler(BaseJobHandler):
    """!
    Pushes data to repo
    """

    def get_job(self):
        return BackgroundJob.JOB_PUSH_YEAR_DATA_TO_REPO

    def process(self, obj=None):
        # TODO read year from string
        try:
            if DataExport.is_year_data_set():
                from .updatemgr import UpdateManager

                update_mgr = UpdateManager(self._config)
                update_mgr.write_and_push_year_data()
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error("Exception: {} {}".format(str(e), error_text))


class PushNoTimeDataToRepoJobHandler(BaseJobHandler):
    """!
    Pushes data to repo
    """

    def get_job(self):
        return BackgroundJob.JOB_PUSH_NOTIME_DATA_TO_REPO

    def process(self, obj=None):
        try:
            if DataExport.is_notime_data_set():
                from .updatemgr import UpdateManager

                update_mgr = UpdateManager(self._config)
                update_mgr.write_and_push_notime_data()
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error("Exception: {} {}".format(str(e), error_text))


class PushDailyDataToRepoJobHandler(BaseJobHandler):
    """!
    Pushes data to repo
    """

    def get_job(self):
        return BackgroundJob.JOB_PUSH_DAILY_DATA_TO_REPO

    def process(self, obj=None):
        # TODO read date from string
        try:
            if DataExport.is_daily_data_set():
                from .updatemgr import UpdateManager

                date_input = obj.subject

                update_mgr = UpdateManager(self._config)
                update_mgr.write_and_push_daily_data(date_input)
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error("Exception: {} {}".format(str(e), error_text))


class CleanupJobHandler(BaseJobHandler):
    """!
    Pushes data to repo
    """

    def get_job(self):
        return BackgroundJob.JOB_CLEANUP

    def process(self, obj=None):
        try:
            LinkDataController.clear_old_entries()
            LinkDataController.move_old_links_to_archive()
            Domains.reset_dynamic_data()
            SourceDataModel.reset_dynamic_data()
            KeyWords.clear()

        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error("Exception: {} {}".format(str(e), error_text))


class CheckDomainsJobHandler(BaseJobHandler):
    def get_job(self):
        return BackgroundJob.JOB_CHECK_DOMAINS

    def process(self, obj=None):
        try:
            Domains.update_all()
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error("Exception: {} {}".format(str(e), error_text))


class RefreshThreadHandler(object):
    """!
    refreshes sources, synchronously.
    This handler only adds background jobs, nothing more
    """

    def refresh(self, item=None):
        # This has to be done before exporting
        KeyWords.clear()

        PersistentInfo.create("Refreshing RSS data")

        from .controllers import SourceDataController

        self.check_sources()

        if SourceExportHistory.is_update_required():
            self.do_update()
            SourceExportHistory.confirm()

        PersistentInfo.create("Refreshing RSS data - done")

    def check_sources(self):
        from .controllers import SourceDataController

        sources = SourceDataController.objects.filter(on_hold=False)
        for source in sources:
            if source.is_fetch_possible():
                BackgroundJobController.download_rss(source)

    def do_update(self):
        if DataExport.is_daily_data_set():
            BackgroundJobController.push_daily_data_to_repo()

        if DataExport.is_year_data_set():
            BackgroundJobController.push_year_data_to_repo()

        if DataExport.is_notime_data_set():
            BackgroundJobController.push_notime_data_to_repo()

        c = Configuration.get_object()
        conf = c.config_entry

        if conf.source_save:
            sources = SourceDataController.objects.filter(on_hold=False)
            for source in sources:
                BackgroundJobController.link_save(source.url)

        BackgroundJobController.make_cleanup()


class HandlerManager(object):
    """!
    @note Uses handler priority when processing jobs.
    """

    def get_handlers(self):
        """
        @returns available handlers. Order is important
        """
        return [
            PushToRepoJobHandler(),
            PushDailyDataToRepoJobHandler(),
            PushYearDataToRepoJobHandler(),
            PushNoTimeDataToRepoJobHandler(),
            ProcessSourceJobHandler(),
            LinkAddJobHandler(),
            LinkDownloadJobHandler(),
            LinkMusicDownloadJobHandler(),
            LinkVideoDownloadJobHandler(),
            LinkSaveJobHandler(),
            WriteDailyDataJobHandler(),
            WriteBookmarksJobHandler(),
            WriteTopicJobHandler(),
            ImportSourcesJobHandler(),
            ImportBookmarksJobHandler(),
            ImportDailyDataJobHandler(),
            ImportInstanceJobHandler(),
            CleanupJobHandler(),
            CheckDomainsJobHandler(),
            EntryUpdateData(),
        ]

    def get_handler_and_object(self):
        afilter = None
        for key, handler in enumerate(self.get_handlers()):
            afilter = handler.get_job_filter()

            objs = BackgroundJob.objects.filter(afilter)
            if objs.count() != 0:
                obj = objs[0]
                return [obj, handler]
        return []

    def process_all(self):
        PersistentInfo.create("Processing messages")

        config = Configuration.get_object()
        start_processing_time = time.time()

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

                # if 10 minutes passed
                if time.time() - start_processing_time >= 60 * 10:
                    break

        PersistentInfo.create("Processing messages done")
