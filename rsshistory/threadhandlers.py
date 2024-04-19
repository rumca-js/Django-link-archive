"""
@brief This file provides handlers for 'jobs'.

Jobs:
  - should do task, not check if task should be done
  - only exception is refresh task, it should verify what additionally should be done
  - BackgroundJob API should verify if task should be done
"""
import logging
import time
import traceback
import json
from datetime import date, datetime, timedelta
from pathlib import Path

from django.db.models import Q
from django.contrib.auth.models import User

from .apps import LinkDatabase
from .models import (
    AppLogging,
    BackgroundJob,
    SourceDataModel,
    SourceExportHistory,
    KeyWords,
    DataExport,
    ConfigurationEntry,
    UserConfig,
    UserTags,
    UserVotes,
    UserBookmarks,
    UserSearchHistory,
    UserEntryTransitionHistory,
    UserEntryVisitHistory,
)

from .pluginsources.sourcecontrollerbuilder import SourceControllerBuilder
from .basictypes import fix_path_for_windows
from .programwrappers import ytdlp, id3v2
from .controllers import (
    BackgroundJobController,
    LinkDataController,
    SourceDataController,
    LinkDataBuilder,
    DomainsController,
    LinkCommentDataController,
    EntriesCleanupAndUpdate,
    EntryUpdater,
)
from .configuration import Configuration
from .dateutils import DateUtils
from .webtools import HtmlPage, DomainAwarePage, ContentLinkParser
from .pluginurl import UrlHandler


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

    def get_input_cfg(self, in_object=None):
        cfg = {}

        if in_object.args and len(in_object.args) > 0:
            try:
                cfg = json.loads(in_object.args)
            except Exception as E:
                AppLogging.error(
                    "Exception when adding link {0} {1} {2}".format(
                        in_object.subject, str(e), error_text
                    )
                )

        return cfg


class ProcessSourceJobHandler(BaseJobHandler):
    """!
    Processes source, checks if contains new entries
    """

    def get_job(self):
        return BackgroundJob.JOB_PROCESS_SOURCE

    def process(self, obj=None):
        try:
            source_url = obj.subject
            sources = SourceDataModel.objects.filter(url=source_url)
            if sources.count() > 0 and not sources[0].enabled:
                # This source is disabled, and job should be removed
                return True

            plugin = SourceControllerBuilder.get(source_url)
            if plugin:
                if plugin.check_for_data():
                    return True

                # TODO implement it differently.
                # it does not have to be the time to download data at all
                # else:
                #    """
                #    We remove the job, then insert new one, if we haven't finished it
                #    """
                #    obj.delete()

                #    sources = SourceDataController.objects.filter(url = obj.subject)
                #    if sources.count() > 0:
                #        source = sources[0]
                #        BackgroundJobController.download_rss(source)

                #    return False
                return True

            AppLogging.error("Cannot find controller plugin for {}".format(obj.subject))
            return False

        except Exception as e:
            error_text = traceback.format_exc()
            AppLogging.error(
                "Exception during parsing page contents {0} {1} {2}".format(
                    obj.subject, str(e), error_text
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

                u = EntryUpdater(entry)
                u.update_data()
            else:
                LinkDatabase.info(
                    "Cannot update data. Missing entry {0}".format(
                        obj.subject,
                    )
                )

            return True
        except Exception as e:
            error_text = traceback.format_exc()
            AppLogging.error(
                "Exception when updating link data {0} {1} {2}".format(
                    obj.subject, str(e), error_text
                )
            )


class LinkResetDataJobHandler(BaseJobHandler):
    def get_job(self):
        return BackgroundJob.JOB_LINK_RESET_DATA

    def process(self, obj=None):
        try:
            entries = LinkDataController.objects.filter(link=obj.subject)
            if len(entries) > 0:
                entry = entries[0]

                u = EntryUpdater(entry)
                u.reset_data()

            return True
        except Exception as e:
            error_text = traceback.format_exc()
            AppLogging.error("Exception: {} {}".format(str(e), error_text))


class LinkResetLocalDataJobHandler(BaseJobHandler):
    def get_job(self):
        return BackgroundJob.JOB_LINK_RESET_LOCAL_DATA

    def process(self, obj=None):
        try:
            entries = LinkDataController.objects.filter(link=obj.subject)
            if len(entries) > 0:
                entry = entries[0]

                u = EntryUpdater(entry)
                u.reset_local_data()

            return True
        except Exception as e:
            error_text = traceback.format_exc()
            AppLogging.error("Exception: {} {}".format(str(e), error_text))


class LinkDownloadJobHandler(BaseJobHandler):
    """!
    downloads entry
    """

    def get_job(self):
        return BackgroundJob.JOB_LINK_DOWNLOAD

    def process(self, obj=None):
        try:
            item = LinkDataController.objects.filter(link=obj.subject)[0]

            p = HtmlPage(item.link)
            p.download_all()

            AppLogging.info("Page has been downloaded:{}".format(item.link))

            return True
        except Exception as e:
            error_text = traceback.format_exc()
            AppLogging.error(
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

            AppLogging.info("Downloading music: " + item.link + " " + item.title)
            # TODO pass dir?

            file_name = Path(str(item.artist)) / str(item.album) / item.title
            file_name = str(file_name) + ".mp3"
            file_name = fix_path_for_windows(file_name)

            yt = ytdlp.YTDLP(item.link)
            if not yt.download_audio(file_name):
                AppLogging.error(
                    "Could not download music: " + item.link + " " + item.title
                )
                return

            data = {"artist": item.artist, "album": item.album, "title": item.title}

            id3 = id3v2.Id3v2(file_name, data)
            id3.tag()
            AppLogging.info("Downloading music done: " + item.link + " " + item.title)

            return True
        except Exception as e:
            error_text = traceback.format_exc()
            AppLogging.error(
                "Exception downloading music {0} {1} {2}".format(
                    obj.subject, str(e), error_text
                )
            )
            return True


class LinkVideoDownloadJobHandler(BaseJobHandler):
    """!
    downloads entry video
    """

    def get_job(self):
        return BackgroundJob.JOB_LINK_DOWNLOAD_VIDEO

    def process(self, obj=None):
        try:
            item = LinkDataController.objects.filter(link=obj.subject)[0]

            AppLogging.info("Downloading video: " + item.link + " " + item.title)

            yt = ytdlp.YTDLP(item.link)
            if not yt.download_video("file.mp4"):
                AppLogging.error(
                    "Could not download video: " + item.link + " " + item.title
                )
                return

            AppLogging.info("Downloading video done: " + item.link + " " + item.title)

            return True
        except Exception as e:
            error_text = traceback.format_exc()
            AppLogging.error(
                "Exception downloading video {0} {1} {2}".format(
                    obj.subject, str(e), error_text
                )
            )
            return True


class LinkAddJobHandler(BaseJobHandler):
    """!
    Adds entry to database
    """

    def get_job(self):
        return BackgroundJob.JOB_LINK_ADD

    def process(self, obj=None):
        """
        Object is obligatory
        """
        try:
            data = self.get_data_for_add(obj)
            self.add_link(data)

            return True

        except Exception as e:
            error_text = traceback.format_exc()
            AppLogging.error(
                "Exception when adding link {0} {1} {2}".format(
                    obj.subject, str(e), error_text
                )
            )
            # remove object from queue if it cannot be added
            return True

    def add_link(self, data):
        # Unpack if link service
        link = data["link"]
        if DomainAwarePage(link).is_link_service():
            h = UrlHandler(link)
            if h.get_contents():
                link = h.response.url
                data["link"] = link

        # Add the link
        b = LinkDataBuilder()
        b.link_data = data
        b.link = link
        b.source_is_auto = True

        entry = b.add_from_link()

        if not entry:
            # TODO send notification?
            LinkDatabase.info("Could not add link: {}".format(data["link"]))
            return True

        current_time = DateUtils.get_datetime_now_utc()

        # if this is a new entry, then tag it
        if entry.date_published:
            if entry.date_published >= current_time:
                if "tag" in data:
                    UserTags.set_tags(entry, tag=data["tag"], user=data["user_object"])

    def get_data_for_add(self, in_object=None):
        link = in_object.subject

        cfg = self.get_input_cfg(in_object)

        data = {"link": link, "bookmarked": False}

        if "properties" in cfg:
            data = cfg["properties"]
            data["link"] = link

        if "source" in cfg:
            source_id = cfg["source"]
            source_objs = SourceDataController.objects.filter(id=int(source_id))
            if source_objs.count() > 0:
                data["source_obj"] = source_objs[0]

        user = None
        if "user_id" in cfg:
            user = User.objects.get(id=int(cfg["user_id"]))
        else:
            users = User.objects.filter(is_superuser=True)
            if users.count() > 0:
                user = users[0]
            else:
                AppLogging.error("Could not found super user")

        data["user_object"] = user

        if "tag" in cfg:
            data["tag"] = cfg["tag"]

        return data


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

            return True
        except Exception as e:
            error_text = traceback.format_exc()
            AppLogging.error(
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

            return True
        except Exception as e:
            error_text = traceback.format_exc()
            AppLogging.error(
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

        return True

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

        return True

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

        return True


class ImportInstanceJobHandler(BaseJobHandler):
    """!
    Imports from instance
    """

    def get_job(self):
        return BackgroundJob.JOB_IMPORT_INSTANCE

    def process(self, obj=None):
        import json

        json_url = obj.subject
        author = obj.args

        from .serializers.instanceimporter import InstanceImporter

        if author != "":
            ie = InstanceImporter(json_url, author)
        else:
            ie = InstanceImporter(json_url)
        ie.import_all()

        return True


class ImportFromFilesJobHandler(BaseJobHandler):
    """!
    Imports from files
    """

    def get_job(self):
        return BackgroundJob.JOB_IMPORT_FROM_FILES

    def process(self, obj=None):
        import json

        data = obj.subject
        data = json.loads(data)

        path = data["path"]
        import_title = data["import_title"]
        import_description = data["import_description"]
        import_tags = data["import_tags"]
        import_votes = data["import_votes"]
        username = data["user"]
        tag = data["tag"]

        user = None
        if username and username != "":
            users = User.objects.filter(username=username)
            if users.count() > 0:
                user = users[0]

        from .serializers import FileImporter

        FileImporter(path=path, user=user)

        return True


class WriteYearDataJobHandler(BaseJobHandler):
    """!
    Writes yearly data to disk
    """

    def get_job(self):
        return BackgroundJob.JOB_WRITE_YEAR_DATA

    def process(self, obj=None):
        try:
            from .updatemgr import UpdateManager

            c = Configuration.get_object()
            mgr = UpdateManager(c)
            mgr.write_year_data()

            return True
        except Exception as e:
            error_text = traceback.format_exc()
            AppLogging.error(
                "Exception: Writing yearly data: {} {}".format(str(e), error_text)
            )


class WriteNoTimeDataJobHandler(BaseJobHandler):
    """!
    Writes yearly data to disk
    """

    def get_job(self):
        return BackgroundJob.JOB_WRITE_NOTIME_DATA

    def process(self, obj=None):
        try:
            from .updatemgr import UpdateManager

            c = Configuration.get_object()
            mgr = UpdateManager(c)
            mgr.write_notime_data()

            return True
        except Exception as e:
            error_text = traceback.format_exc()
            AppLogging.error(
                "Exception: Writing notime: {} {}".format(str(e), error_text)
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

            return True
        except Exception as e:
            error_text = traceback.format_exc()
            AppLogging.error(
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
            AppLogging.error("Exception: {} {}".format(str(e), error_text))


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

            return True
        except Exception as e:
            error_text = traceback.format_exc()
            AppLogging.error("Exception: {} {}".format(str(e), error_text))


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

            return True
        except Exception as e:
            error_text = traceback.format_exc()
            AppLogging.error("Exception: {} {}".format(str(e), error_text))


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

            return True
        except Exception as e:
            error_text = traceback.format_exc()
            AppLogging.error(
                "Push daily data exception: {} {}".format(str(e), error_text)
            )


class CleanupJobHandler(BaseJobHandler):
    """!
    Pushes data to repo
    """

    def get_job(self):
        return BackgroundJob.JOB_CLEANUP

    def process(self, obj=None):
        try:
            limit = 0
            try:
                if obj is not None:
                    limit = int(obj.subject)
            except Exception as E:
                LinkDatabase.info("Cleanup, cannot read limit value:{}".format(str(E)))

            status = EntriesCleanupAndUpdate().cleanup()

            if limit == 0:
                SourceDataController.cleanup()

                AppLogging.cleanup()
                DomainsController.cleanup()
                KeyWords.cleanup()
                UserConfig.cleanup()

                self.user_tables_cleanup()

            # if status is True, everything has been cleared correctly
            # we can remove the cleanup background job
            return status

        except Exception as e:
            error_text = traceback.format_exc()
            AppLogging.error("Cleanup exception: {} {}".format(str(e), error_text))

    def user_tables_cleanup(self):
        UserTags.cleanup()
        LinkCommentDataController.cleanup()
        UserVotes.cleanup()
        UserBookmarks.cleanup()
        UserSearchHistory.cleanup()
        UserEntryTransitionHistory.cleanup()
        UserEntryVisitHistory.cleanup()


class CheckDomainsJobHandler(BaseJobHandler):
    def get_job(self):
        return BackgroundJob.JOB_CHECK_DOMAINS

    def process(self, obj=None):
        try:
            DomainsController.update_all()

            return True
        except Exception as e:
            error_text = traceback.format_exc()
            AppLogging.error("Exception: {} {}".format(str(e), error_text))


class LinkScanJobHandler(BaseJobHandler):
    def get_job(self):
        return BackgroundJob.JOB_LINK_SCAN

    def process(self, obj=None):
        try:
            link = obj.subject

            cfg = self.get_input_cfg(obj)
            source = None

            if "source" in cfg:
                source_id = cfg["source"]
                source_objs = SourceDataController.objects.filter(id=int(source_id))
                if source_objs.count() > 0:
                    source = source_objs[0]

            p = UrlHandler(link)
            contents = p.get_contents()

            p = ContentLinkParser(link, contents)

            c = Configuration.get_object()
            conf = c.config_entry

            if conf.auto_store_domain_info:
                links = p.get_domains()
                for link in links:
                    BackgroundJobController.link_add(link, source=source)

            if conf.auto_store_entries:
                links = p.get_links()
                for link in links:
                    BackgroundJobController.link_add(link, source=source)

            return True
        except Exception as e:
            error_text = traceback.format_exc()
            AppLogging.error("Exception: {} {}".format(str(e), error_text))


class MoveToArchiveJobHandler(BaseJobHandler):
    def get_job(self):
        return BackgroundJob.JOB_MOVE_TO_ARCHIVE

    def process(self, obj=None):
        try:
            LinkDataController.move_old_links_to_archive()

            return True
        except Exception as e:
            error_text = traceback.format_exc()
            AppLogging.error("Exception: {} {}".format(str(e), error_text))


class RefreshThreadHandler(object):
    """!
    Checks if tasks should be created.

    @note This handler only adds background jobs, nothing more!
    """

    def refresh(self, item=None):
        # some settings in config could have changed
        # if we run celery - process need to fetch new settings
        c = Configuration.get_object()
        c.config_entry = ConfigurationEntry.get()

        from .controllers import SourceDataController

        self.check_sources()

        if SourceExportHistory.is_update_required():
            self.do_update()
            SourceExportHistory.confirm()

    def check_sources(self):
        from .controllers import SourceDataController

        sources = SourceDataController.objects.filter(enabled=True).order_by(
            "dynamic_data__date_fetched"
        )
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
            sources = SourceDataController.objects.filter(enabled=True)
            for source in sources:
                BackgroundJobController.link_save(source.url)

        BackgroundJobController.make_cleanup()


class HandlerManager(object):
    """!
    @note Uses handler priority when processing jobs.
    """

    def __init__(self, timeout_s=60 * 10):
        """
        Default timeout is 10 minutes
        """
        self.timeout_s = timeout_s

    def get_handlers(self):
        """
        @returns available handlers. Order is important
        """
        return [
            # fmt: off
            PushToRepoJobHandler(),

            PushDailyDataToRepoJobHandler(),
            PushYearDataToRepoJobHandler(),
            PushNoTimeDataToRepoJobHandler(),

            WriteDailyDataJobHandler(),
            WriteYearDataJobHandler(),
            WriteNoTimeDataJobHandler(),
            WriteTopicJobHandler(),

            ImportSourcesJobHandler(),
            ImportBookmarksJobHandler(),
            ImportDailyDataJobHandler(),
            ImportInstanceJobHandler(),
            ImportFromFilesJobHandler(),

            CleanupJobHandler(),
            MoveToArchiveJobHandler(),
            ProcessSourceJobHandler(),
            LinkAddJobHandler(),
            LinkScanJobHandler(),
            LinkResetDataJobHandler(),
            LinkResetLocalDataJobHandler(),
            LinkDownloadJobHandler(),
            LinkMusicDownloadJobHandler(),
            LinkVideoDownloadJobHandler(),
            EntryUpdateData(),
            LinkSaveJobHandler(),
            CheckDomainsJobHandler(),
            # fmt: on
        ]

    def get_handler_and_object(self):
        """
        TODO select should be based on priority
        """

        objs = BackgroundJobController.objects.filter(enabled=True).order_by(
            "priority", "date_created"
        )
        if objs.count() != 0:
            obj = objs[0]

            for key, handler in enumerate(self.get_handlers()):
                if handler.get_job() == obj.job:
                    return [obj, handler]
            return [obj, None]
        return []

    def process_all(self):
        self.start_processing_time = DateUtils.get_datetime_now_utc()

        while True:
            items = self.get_handler_and_object()
            if len(items) == 0:
                break

            self.process_one_for_all(items)

            passed_seconds = (
                DateUtils.get_datetime_now_utc() - self.start_processing_time
            )
            if passed_seconds.total_seconds() >= self.timeout_s:
                obj = items[0]
                handler = items[1]
                text = "Threads: last handler {} {} exceeded time:{}".format(
                    handler.get_job(), obj.subject, passed_seconds
                )
                AppLogging.error(text)

                self.on_not_safe_exit(items)
                break

    def process_one_for_all(self, items):
        config = Configuration.get_object()

        obj = items[0]
        handler = items[1]
        subject = obj.subject
        deleted = False

        if handler:
            handler.set_config(config)

        try:
            if handler and handler.process(obj):
                deleted = True
                obj.delete()
            if not handler:
                AppLogging.error(
                    "Missing handler for job: {0}".format(
                        obj.job,
                    )
                )
                deleted = True
                obj.delete()

        except Exception as E:
            error_text = traceback.format_exc()
            AppLogging.error(
                "Exception during handler processing job:{}\nsubject:{}\nException:{}\nError text:{}".format(
                    obj.job, obj.subject, str(E), error_text
                )
            )
            if not deleted and obj:
                obj.on_error()

    def on_not_safe_exit(self, items):
        jobs = BackgroundJobController.objects.filter(
            date_created__lt=self.start_processing_time
        )
        for job in jobs:
            if job.priority > 0:
                job.priority -= 1
                job.save()

    def process_one(self):
        """
        TODO remove this function, use process_one_for_all one above
        """
        AppLogging.info("Processing message")

        config = Configuration.get_object()
        start_processing_time = time.time()

        items = self.get_handler_and_object()
        if len(items) == 0:
            return False

        self.process_one_for_all(items)

        items = self.get_handler_and_object()
        if len(items) == 0:
            return False

        AppLogging.info("Processing messages done")

        return True
