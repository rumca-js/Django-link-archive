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
    CompactedTags,
    UserVotes,
    UserBookmarks,
    UserSearchHistory,
    UserEntryTransitionHistory,
    UserEntryVisitHistory,
    ModelFiles,
    SystemOperation,
)

from .pluginsources.sourcecontrollerbuilder import SourceControllerBuilder
from .basictypes import fix_path_for_windows
from .programwrappers import ytdlp, id3v2
from .controllers import (
    BackgroundJobController,
    LinkDataController,
    SourceDataController,
    EntryDataBuilder,
    DomainsController,
    LinkCommentDataController,
    EntriesCleanupAndUpdate,
    EntryUpdater,
    EntriesUpdater,
    EntryScanner,
    ModelFilesBuilder,
)
from .configuration import Configuration
from .dateutils import DateUtils
from .webtools import HtmlPage, DomainAwarePage, ContentLinkParser, BasePage
from .pluginurl import UrlHandler


class BaseJobHandler(object):
    """!
    Base handler
    """

    def __init__(self, config=None):
        self._config = config
        self.start_processing_time = DateUtils.get_datetime_now_utc()

    def get_time_diff(self):
        """
        To obtain difference in seconds call total_seconds()
        """
        return (DateUtils.get_datetime_now_utc() - self.start_processing_time)

    def get_time_diff_sec(self):
        """
        To obtain difference in seconds call total_seconds()
        """
        return self.get_time_diff().total_seconds()

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
                AppLogging.exc(exception_object = E,
                    info_text = "Exception when adding link {0}".format(
                        in_object.subject
                    )
                )

        return cfg


class ProcessSourceJobHandler(BaseJobHandler):
    """!
    Processes source, checks if contains new entries
    """

    def get_job():
        return BackgroundJob.JOB_PROCESS_SOURCE

    def process(self, obj=None):
        try:
            try:
                source_id = int(obj.subject)
            except Exception as E:
                AppLogging.exc(exception_object = E, info_text="Incorrect source ID:{}".format(obj.subject))

                obj.enabled = False
                obj.save()

                return False

            sources = SourceDataModel.objects.filter(id=source_id)
            if sources.count() > 0 and not sources[0].enabled:
                # This source is disabled, and job should be removed
                return True

            source = sources[0]

            plugin = SourceControllerBuilder.get(source_id)
            if plugin:
                if plugin.check_for_data():
                    elapsed_sec = self.get_time_diff_sec()
                    AppLogging.debug("Processed source:{}. Time[s]:{}".format(source.url, elapsed_sec))

                    return True
                return True

            AppLogging.error("Cannot find controller plugin for source:{}".format(obj.subject))
            return False

        except Exception as E:
            AppLogging.exc(exception_object = E, 
                info_text = "Exception during parsing page contents {0} {1} {2}".format(obj.subject)
            )


class EntryUpdateData(BaseJobHandler):
    """!
    downloads entry
    """

    def get_job():
        return BackgroundJob.JOB_LINK_UPDATE_DATA

    def process(self, obj=None):
        try:
            link_id = None

            try:
                link_id = int(obj.subject)
            except Exception as E:
                AppLogging.exc(exception_object = E, info_text="Incorrect link ID:{}".format(obj.subject))
                # consume job
                return True

            entries = LinkDataController.objects.filter(id=link_id)
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
        except Exception as E:
            AppLogging.exc(exception_object = E, 
                info_text = "Exception when updating link data {0} {1} {2}".format(obj.subject)
            )


class LinkResetDataJobHandler(BaseJobHandler):
    def get_job():
        return BackgroundJob.JOB_LINK_RESET_DATA

    def process(self, obj=None):
        try:
            try:
                link_id = int(obj.subject)
            except Exception as E:
                AppLogging.exc(exception_object = E, info_text = "Incorrect link ID:{}".format(obj.subject))
                # consume job
                return True

            entries = LinkDataController.objects.filter(id=link_id)
            if len(entries) > 0:
                entry = entries[0]

                u = EntryUpdater(entry)
                u.reset_data()

            return True
        except Exception as E:
            AppLogging.exc(exception_object = E,)


class LinkResetLocalDataJobHandler(BaseJobHandler):
    def get_job():
        return BackgroundJob.JOB_LINK_RESET_LOCAL_DATA

    def process(self, obj=None):
        try:
            try:
                link_id = int(obj.subject)
            except Exception as E:
                AppLogging.exc(exception_object = E, info_text = "Incorrect link ID:{}".format(obj.subject))
                # consume job
                return True

            entries = LinkDataController.objects.filter(id=link_id)
            if len(entries) > 0:
                entry = entries[0]

                u = EntryUpdater(entry)
                u.reset_local_data()

            return True
        except Exception as E:
            AppLogging.exc(exception_object = E,)


class LinkDownloadJobHandler(BaseJobHandler):
    """!
    downloads entry
    """

    def get_job():
        return BackgroundJob.JOB_LINK_DOWNLOAD

    def process(self, obj=None):
        try:
            url = obj.subject

            Url.download_all(url)

            AppLogging.notify("Page has been downloaded:{} Time[s]:{}".format(url, self.get_time_diff_sec()))

            return True
        except Exception as E:
            AppLogging.exc(exception_object = E,
                info_text = "Exception downloading web page {0}".format(obj.subject)
            )


class LinkMusicDownloadJobHandler(BaseJobHandler):
    """!
    downloads entry music
    """

    def get_job():
        return BackgroundJob.JOB_LINK_DOWNLOAD_MUSIC

    def process(self, obj=None):
        try:
            data = self.get_data(obj)

            url = data["url"]
            title = data["title"]
            artist = data["artist"]
            album = data["album"]

            if not DomainAwarePage(url).is_youtube():
                AppLogging.error("Unsupported download operation URL:{}".format(url))
                return True

            AppLogging.info("Downloading music: " + url + " " + title)

            file_name = self.get_file_name(data)

            yt = ytdlp.YTDLP(url)
            if not yt.download_audio(file_name):
                AppLogging.error(
                    "Could not download music: " + url + " " + title
                )
                return

            id3 = id3v2.Id3v2(file_name, data)
            id3.tag()

            elapsed_sec = self.get_time_diff_sec()

            AppLogging.notify("Downloading music done: {} {}. Time[s]:{}".format(url, title, elapsed_sec))

            return True
        except Exception as E:
            AppLogging.exc(exception_object = E,
                info_text = "Exception downloading music {0}".format(
                    obj.subject
                )
            )
            return True

    def get_data(self, obj):
        title = ""
        artist = None
        album = None

        url = obj.subject

        entries = LinkDataController.objects.filter(link=url)
        if entries.exists():
            entry = entries[0]
            title = entry.title
            artist = entry.artist
            album = entry.album

        data = {"artist": str(artist), "album": str(album), "title": str(title), "url" : url}

        return data

    def get_file_name(self, data):
        file_name = Path(str(data["title"]) + ".mp3")
        if data["album"]:
            file_name = Path(data["album"]) / file_name

        if data["artist"]:
            file_name = Path(data["artist"]) / file_name

        file_name = fix_path_for_windows(file_name)

        return file_name


class LinkVideoDownloadJobHandler(BaseJobHandler):
    """!
    downloads entry video
    """

    def get_job():
        return BackgroundJob.JOB_LINK_DOWNLOAD_VIDEO

    def process(self, obj=None):
        try:
            data = self.get_data(obj)

            url = data["url"]
            title = data["title"]
            artist = data["artist"]
            album = data["album"]

            if not DomainAwarePage(url).is_youtube():
                AppLogging.error("Unsupported download operation URL:{}".format(url))
                return True

            AppLogging.info("Downloading music: " + url + " " + title)

            file_name = self.get_file_name(data)

            yt = ytdlp.YTDLP(url)
            if not yt.download_video("file.mp4"):
                AppLogging.error(
                    "Could not download video: " + url + " " + title
                )
                return

            elapsed_sec = self.get_time_diff_sec()
            AppLogging.notify("Downloading video done: {} {}. Time[s]:{}".format(url, title, elapsed_sec))

            return True
        except Exception as E:
            AppLogging.exc(exception_object = E,
                info_text = "Exception downloading video {0}".format(
                    obj.subject
                )
            )
            return True

    def get_data(self, obj):
        title = ""
        artist = None
        album = None

        url = obj.subject

        entries = LinkDataController.objects.filter(link=url)
        if entries.exists():
            entry = entries[0]
            title = entry.title
            artist = entry.artist
            album = entry.album

        data = {"artist": str(artist), "album": str(album), "title": str(title), "url" : url}

        return data

    def get_file_name(self, data):
        file_name = Path(str(data["title"]) + ".mp3")
        if data["album"]:
            file_name = Path(data["album"]) / file_name

        if data["artist"]:
            file_name = Path(data["artist"]) / file_name

        file_name = fix_path_for_windows(file_name)

        return file_name


class DownloadModelFileJobHandler(BaseJobHandler):
    """!
    downloads entry video
    """

    def get_job():
        return BackgroundJob.JOB_DOWNLOAD_FILE

    def process(self, obj=None):
        try:
            c = Configuration.get_object()
            if not c.config_entry.enable_file_support:
                # consume
                return True

            file_name = obj.subject
            p = DomainAwarePage(file_name)
            if not p.is_web_link():
                # consume
                return True

            ModelFilesBuilder().build(file_name)

            return True
        except Exception as E:
            AppLogging.exc(exception_object = E,
                info_text = "Exception downloading file {0} {1} {2}".format(
                    obj.subject
                )
            )
            return True


class LinkAddJobHandler(BaseJobHandler):
    """!
    Adds entry to database
    """

    def get_job():
        return BackgroundJob.JOB_LINK_ADD

    def process(self, obj=None):
        """
        Object is obligatory
        """
        try:
            data = self.get_data_for_add(obj)
            self.add_link(data)

            return True

        except Exception as E:
            AppLogging.exc(exception_object = E,
                info_text = "Exception when adding link {0}".format(obj.subject)
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
        b = EntryDataBuilder()
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

        if "source_id" in cfg:
            source_id = cfg["source_id"]
            source_objs = SourceDataController.objects.filter(id=int(source_id))
            if source_objs.count() > 0:
                data["source_obj"] = source_objs[0]

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

    def get_job():
        return BackgroundJob.JOB_LINK_SAVE

    def process(self, obj=None):
        try:
            item = obj.subject

            from .services.waybackmachine import WaybackMachine

            wb = WaybackMachine()
            if wb.is_saved(item):
                wb.save(item)

            return True
        except Exception as E:
            AppLogging.exc(exception_object = E,)


class WriteDailyDataJobHandler(BaseJobHandler):
    """!
    Writes daily data to disk
    """

    def get_job():
        return BackgroundJob.JOB_WRITE_DAILY_DATA

    def process(self, obj=None):
        try:
            from .updatemgr import UpdateManager
            from .datawriter import DataWriter

            date_input = datetime.strptime(obj.subject, "%Y-%m-%d").date()

            update_mgr = UpdateManager(self._config)
            update_mgr.write_daily_data(date_input.isoformat())

            return True
        except Exception as E:
            AppLogging.exc(exception_object = E,)


class ImportDailyDataJobHandler(BaseJobHandler):
    """!
    Writes daily data to disk
    """

    def get_job():
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

    def get_job():
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

    def get_job():
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

    def get_job():
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

    def get_job():
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

    def get_job():
        return BackgroundJob.JOB_WRITE_YEAR_DATA

    def process(self, obj=None):
        try:
            from .updatemgr import UpdateManager

            c = Configuration.get_object()
            mgr = UpdateManager(c)
            mgr.write_year_data()

            return True
        except Exception as E:
            AppLogging.exc(exception_object = E,)


class WriteNoTimeDataJobHandler(BaseJobHandler):
    """!
    Writes yearly data to disk
    """

    def get_job():
        return BackgroundJob.JOB_WRITE_NOTIME_DATA

    def process(self, obj=None):
        try:
            from .updatemgr import UpdateManager

            c = Configuration.get_object()
            mgr = UpdateManager(c)
            mgr.write_notime_data()

            return True
        except Exception as E:
            AppLogging.exc(exception_object = E,)


class WriteTopicJobHandler(BaseJobHandler):
    """!
    Writes topic data to disk
    """

    def get_job():
        return BackgroundJob.JOB_WRITE_TOPIC_DATA

    def process(self, obj=None):
        try:
            from ..serializers.bookmarksexporter import BookmarksTopicExporter
            topic = obj.subject

            c = Configuration.get_object()
            exporter = BookmarksTopicExporter(c)
            exporter.export(topic)

            return True
        except Exception as E:
            AppLogging.exc(exception_object = E,)


class ExportDataJobHandler(BaseJobHandler):
    """!
    Pushes data to repo
    """

    def get_job():
        return BackgroundJob.JOB_EXPORT_DATA

    def process(self, obj=None):
        from .updatemgr import UpdateManager

        try:
            export = self.get_export(obj)
            if not export:
                return

            update_mgr = UpdateManager(self._config)

            if export.is_daily_data():
                update_mgr.write_and_push_daily_data()
            if export.is_year_data():
                update_mgr.write_and_push_year_data()
            if export.is_notime_data():
                update_mgr.write_and_push_notime_data()

            SourceExportHistory.confirm(export)

            elapsed_sec = self.get_time_diff_sec()
            AppLogging.notify("Successfully pushed data to git. Time[s]:{}".format(elapsed_sec))

            return True
        except Exception as E:
            AppLogging.exc(exception_object = E,)

    def get_export(self, obj):
        exports = DataExport.objects.filter(id=int(obj.subject))
        if exports.count() > 0:
            return exports[0]


class PushYearDataToRepoJobHandler(BaseJobHandler):
    """!
    Pushes data to repo
    """

    def get_job():
        return BackgroundJob.JOB_PUSH_YEAR_DATA_TO_REPO

    def process(self, obj=None):
        # TODO read year from string
        try:
            if DataExport.is_year_data_set():
                from .updatemgr import UpdateManager

                update_mgr = UpdateManager(self._config)
                update_mgr.write_and_push_year_data()

                elapsed_sec = self.get_time_diff_sec()
                AppLogging.notify("Successfully pushed data to git. Time[s]:{}".format(elapsed_sec))

            return True
        except Exception as E:
            AppLogging.exc(exception_object = E,)


class PushNoTimeDataToRepoJobHandler(BaseJobHandler):
    """!
    Pushes data to repo
    """

    def get_job():
        return BackgroundJob.JOB_PUSH_NOTIME_DATA_TO_REPO

    def process(self, obj=None):
        try:
            if DataExport.is_notime_data_set():
                from .updatemgr import UpdateManager

                update_mgr = UpdateManager(self._config)
                update_mgr.write_and_push_notime_data()

                elapsed_sec = self.get_time_diff_sec()
                AppLogging.notify("Successfully pushed data to git. Time[s]:{}".format(elapsed_sec))

            return True
        except Exception as E:
            AppLogging.exc(exception_object = E,)


class PushDailyDataToRepoJobHandler(BaseJobHandler):
    """!
    Pushes data to repo
    """

    def get_job():
        return BackgroundJob.JOB_PUSH_DAILY_DATA_TO_REPO

    def process(self, obj=None):
        # TODO read date from string
        try:
            if DataExport.is_daily_data_set():
                from .updatemgr import UpdateManager

                date_input = obj.subject

                update_mgr = UpdateManager(self._config)
                update_mgr.write_and_push_daily_data(date_input)

                elapsed_sec = self.get_time_diff_sec()
                AppLogging.notify("Successfully pushed data to git. Time[s]:{}".format(elapsed_sec))

            return True
        except Exception as E:
            AppLogging.exc(exception_object = E,)


class CleanupJobHandler(BaseJobHandler):
    """!
    Pushes data to repo
    """

    def get_job():
        return BackgroundJob.JOB_CLEANUP

    def process(self, obj=None):
        try:
            limit_s = 0
            try:
                if obj is not None:
                    limit_s = int(obj.subject)
            except Exception as E:
                AppLogging.debug("Cleanup, cannot read limit value:{}".format(str(E)))

            status = EntriesCleanupAndUpdate().cleanup(limit_s)

            if limit_s == 0:
                SourceDataController.cleanup()

                AppLogging.cleanup()
                DomainsController.cleanup()
                KeyWords.cleanup()
                UserConfig.cleanup()
                SourceExportHistory.cleanup()
                ModelFiles.cleanup()
                SystemOperation.cleanup()

                self.user_tables_cleanup()

            # if status is True, everything has been cleared correctly
            # we can remove the cleanup background job

            elapsed_sec = self.get_time_diff_sec()
            AppLogging.notify("Successfully cleaned database. Time[s]:{}".format(elapsed_sec))
            return status

        except Exception as E:
            AppLogging.exc(exception_object = E,)

    def user_tables_cleanup(self):
        UserTags.cleanup()
        CompactedTags.cleanup()
        LinkCommentDataController.cleanup()
        UserVotes.cleanup()
        UserBookmarks.cleanup()
        UserSearchHistory.cleanup()
        UserEntryTransitionHistory.cleanup()
        UserEntryVisitHistory.cleanup()


class CheckDomainsJobHandler(BaseJobHandler):
    def get_job():
        return BackgroundJob.JOB_CHECK_DOMAINS

    def process(self, obj=None):
        try:
            DomainsController.update_all()

            return True
        except Exception as E:
            AppLogging.exc(exception_object = E,)


class LinkScanJobHandler(BaseJobHandler):
    def get_job():
        return BackgroundJob.JOB_LINK_SCAN

    def process(self, obj=None):
        try:
            link = obj.subject

            cfg = self.get_input_cfg(obj)
            source = None
            entry = None

            if "source_id" in cfg:
                source_id = cfg["source_id"]
                source_objs = SourceDataController.objects.filter(id=int(source_id))
                if source_objs.count() > 0:
                    source = source_objs[0]

            if "entry_id" in cfg:
                entry_id = cfg["entry_id"]
                entries = LinkDataController.objects.filter(id=int(entry_id))
                if entries.count() > 0:
                    entry = entries[0]

            if "source" in cfg:
                source_id = cfg["source"]
                source_objs = SourceDataController.objects.filter(id=int(source_id))
                if source_objs.count() > 0:
                    source = source_objs[0]

            if "entry" in cfg:
                entry_id = cfg["entry"]
                entries = LinkDataController.objects.filter(id=int(entry_id))
                if entries.count() > 0:
                    entry = entries[0]

            p = UrlHandler(link)
            contents = p.get_contents()

            if entry:
                scanner = EntryScanner(entry=entry, contents=contents)
                scanner.run()
            else:
                scanner = EntryScanner(url=link, contents=contents)
                scanner.run()

            return True
        except Exception as E:
            AppLogging.exc(exception_object = E,)


class MoveToArchiveJobHandler(BaseJobHandler):
    def get_job():
        return BackgroundJob.JOB_MOVE_TO_ARCHIVE

    def process(self, obj=None):
        try:
            LinkDataController.move_old_links_to_archive()

            return True
        except Exception as E:
            AppLogging.exc(exception_object = E,)


class RefreshThreadHandler(object):
    """!
    Checks if tasks should be created.

    @note This handler only adds background jobs, nothing more!
    """

    def refresh(self, item=None):
        c = Configuration.get_object()
        c.refresh(0)

        if not SystemOperation.is_internet_ok():
            return

        from .controllers import SourceDataController

        self.check_sources()

        for export in DataExport.objects.all():
            if SourceExportHistory.is_update_required(export):
                self.do_update(export)
                SourceExportHistory.confirm(export)

        self.update_entries()

    def check_sources(self):
        sources = SourceDataController.objects.filter(enabled=True).order_by(
            "dynamic_data__date_fetched"
        )
        for source in sources:
            if source.is_fetch_possible():
                BackgroundJobController.download_rss(source)

    def do_update(self, export):
        BackgroundJobController.export_data(export)

        c = Configuration.get_object()
        conf = c.config_entry

        if conf.source_save:
            sources = SourceDataController.objects.filter(enabled=True)
            for source in sources:
                BackgroundJobController.link_save(source.url)

        BackgroundJobController.make_cleanup()

    def update_entries(self):
        c = Configuration.get_object()
        conf = c.config_entry

        max_number_of_update_entries = conf.number_of_update_entries

        if max_number_of_update_entries == 0:
            return

        u = EntriesUpdater()
        entries = u.get_entries_to_update()
        if not entries:
            return

        number_of_entries = entries.count()

        if entries and number_of_entries > 0:
            current_num_of_jobs = (
                BackgroundJobController.get_number_of_update_reset_jobs()
            )

            if current_num_of_jobs >= max_number_of_update_entries:
                return

            jobs_to_add = max_number_of_update_entries - current_num_of_jobs
            jobs_to_add = min(jobs_to_add, number_of_entries)

            for index in range(jobs_to_add):
                BackgroundJobController.entry_update_data(entries[index])


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
            ExportDataJobHandler,

            WriteDailyDataJobHandler,
            WriteYearDataJobHandler,
            WriteNoTimeDataJobHandler,
            WriteTopicJobHandler,

            ImportSourcesJobHandler,
            ImportBookmarksJobHandler,
            ImportDailyDataJobHandler,
            ImportInstanceJobHandler,
            ImportFromFilesJobHandler,

            CleanupJobHandler,
            MoveToArchiveJobHandler,
            ProcessSourceJobHandler,
            LinkAddJobHandler,
            LinkScanJobHandler,
            LinkResetDataJobHandler,
            LinkResetLocalDataJobHandler,
            LinkDownloadJobHandler,
            LinkMusicDownloadJobHandler,
            LinkVideoDownloadJobHandler,
            DownloadModelFileJobHandler,
            EntryUpdateData,
            LinkSaveJobHandler,
            CheckDomainsJobHandler,
            # fmt: on
        ]

    def process_all(self):
        try:
            self.start_processing_time = DateUtils.get_datetime_now_utc()

            c = Configuration.get_object()
            c.refresh(1)

            if not SystemOperation.is_internet_ok():
                return

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
        except Exception as E:
            AppLogging.exc(exception_object = E,)

    def process_one_for_all(self, items):
        config = Configuration.get_object()

        obj = items[0]
        handler_class = items[1]
        handler = None
        subject = obj.subject
        deleted = False

        if handler_class:
            handler = handler_class(config)

        try:
            if handler and handler.process(obj):
                deleted = True
                if obj:
                    obj.delete()
            if not handler:
                if obj:
                    AppLogging.error(
                        "Missing handler for job: {0}".format(
                            obj.job,
                        )
                    )
                deleted = True
                if obj:
                    obj.delete()

            if not config.config_entry.debug_mode:
                if not deleted and obj:
                    obj.delete()
                    deleted = True

        except Exception as E:
            error_text = traceback.format_exc()
            if not deleted and obj:
                AppLogging.exc(
                    exception_object = E,
                    info_text = "Job:{}, Subject:{}".format(
                        obj.job, obj.subject
                    )
                )
                obj.on_error()
            else:
                AppLogging.exc(exception_object = E,)

    def process_one(self):
        """
        TODO remove this function, use process_one_for_all one above
        """
        try:
            AppLogging.debug("Processing message")

            config = Configuration.get_object()
            start_processing_time = time.time()

            items = self.get_handler_and_object()
            if len(items) == 0:
                return False

            self.process_one_for_all(items)

            items = self.get_handler_and_object()
            if len(items) == 0:
                return False

            AppLogging.debug("Processing messages done")
        except Exception as E:
            AppLogging.exc(exception_object = E,)

        return True

    def get_handler_and_object(self):
        """
        TODO select should be based on priority
        """

        objs = BackgroundJobController.objects.filter(enabled=True).order_by(
            "priority", "date_created"
        )
        if objs.count() != 0:
            obj = objs[0]

            for key, handler_class in enumerate(self.get_handlers()):
                if handler_class.get_job() == obj.job:
                    return [obj, handler_class]
            return [obj, None]
        return []

    def on_not_safe_exit(self, items):
        blocker = items[0]
        if not blocker:
            return

        jobs = BackgroundJobController.objects.filter(
            enabled=True, date_created__lt=self.start_processing_time
        )
        for job in jobs:
            if job != blocker and job.priority > 0:
                if job.priority > blocker.priority:
                    job.priority = blocker.priority - 1
                else:
                    job.priority -= 1
                    job.save()
