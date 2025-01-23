"""
@brief This file provides handlers for 'jobs'.

Jobs:
  - should do task, not check if task should be done
  - only exception is refresh task, it should verify what additionally should be done
  - BackgroundJob API should verify if task should be done
"""

import json
from datetime import date, datetime
from pathlib import Path

from django.db.models import Q
from django.contrib.auth.models import User
from django.core.paginator import Paginator

from utils.dateutils import DateUtils
from .webtools import UrlLocation, Url

from utils.basictypes import fix_path_for_os
from utils.programwrappers import ytdlp, id3v2, wget

from utils.services.waybackmachine import WaybackMachine

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
    UserCompactedTags,
    UserVotes,
    UserBookmarks,
    UserSearchHistory,
    UserEntryTransitionHistory,
    UserEntryVisitHistory,
    ModelFiles,
    SystemOperation,
    BlockEntryList,
    Gateway,
)

from .pluginsources.sourcecontrollerbuilder import SourceControllerBuilder
from .controllers import (
    BackgroundJobController,
    LinkDataController,
    SourceDataController,
    EntryDataBuilder,
    DomainsController,
    UserCommentsController,
    EntriesCleanupAndUpdate,
    EntryUpdater,
    EntriesUpdater,
    EntryScanner,
    ModelFilesBuilder,
)
from .configuration import Configuration
from .pluginurl import UrlHandlerEx
from .serializers import JsonImporter


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
        return DateUtils.get_datetime_now_utc() - self.start_processing_time

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
            except ValueError as E:
                AppLogging.exc(
                    exception_object=E,
                    info_text="Exception when adding link {0}".format(
                        in_object.subject
                    ),
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
            source_id = int(obj.subject)
        except ValueError as E:
            AppLogging.exc(
                exception_object=E,
                info_text="Incorrect source ID:{}".format(obj.subject),
            )

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
                elapsed_sec = self.get_time_diff()
                AppLogging.debug("Url:{}. Time:{}".format(source.url, elapsed_sec))

                return True
            return True

        AppLogging.error(
            "Source:{}. Cannot find controller plugin for source".format(obj.subject)
        )
        return False


class EntryUpdateData(BaseJobHandler):
    """!
    downloads entry
    """

    def get_job():
        return BackgroundJob.JOB_LINK_UPDATE_DATA

    def process(self, obj=None):
        link_id = None

        try:
            link_id = int(obj.subject)
        except ValueError as E:
            AppLogging.exc(
                exception_object=E,
                info_text="Incorrect link ID:{}".format(obj.subject),
            )
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


class LinkResetDataJobHandler(BaseJobHandler):
    def get_job():
        return BackgroundJob.JOB_LINK_RESET_DATA

    def process(self, obj=None):
        try:
            link_id = int(obj.subject)
        except ValueError as E:
            AppLogging.exc(
                exception_object=E,
                info_text="Incorrect link ID:{}".format(obj.subject),
            )
            # consume job
            return True

        entries = LinkDataController.objects.filter(id=link_id)
        if len(entries) > 0:
            entry = entries[0]

            u = EntryUpdater(entry)
            u.reset_data()

        return True


class LinkResetLocalDataJobHandler(BaseJobHandler):
    def get_job():
        return BackgroundJob.JOB_LINK_RESET_LOCAL_DATA

    def process(self, obj=None):
        try:
            link_id = int(obj.subject)
        except ValueError as E:
            AppLogging.exc(
                exception_object=E,
                info_text="Incorrect link ID:{}".format(obj.subject),
            )
            # consume job
            return True

        entries = LinkDataController.objects.filter(id=link_id)
        if len(entries) > 0:
            entry = entries[0]

            u = EntryUpdater(entry)
            u.reset_local_data()

        return True


class LinkDownloadJobHandler(BaseJobHandler):
    """!
    downloads entry
    """

    def get_job():
        return BackgroundJob.JOB_LINK_DOWNLOAD

    def process(self, obj=None):
        path = ConfigurationEntry.get().get_download_path()

        url = obj.subject
        AppLogging.notify("Downloading page:".format(url))

        wget = wget.Wget(url, cwd=path)
        wget.download_all()

        AppLogging.notify(
            "Page has been downloaded:{} Time:{}".format(url, self.get_time_diff())
        )

        return True


class LinkMusicDownloadJobHandler(BaseJobHandler):
    """!
    downloads entry music
    """

    def get_job():
        return BackgroundJob.JOB_LINK_DOWNLOAD_MUSIC

    def process(self, obj=None):
        c = Configuration.get_object()
        data = self.get_data(obj)

        url = data["url"]
        title = data["title"]
        author = data["author"]
        album = data["album"]

        AppLogging.notify("Downloading music: " + url + " " + title)

        if not UrlLocation(url).is_youtube():
            AppLogging.error("Unsupported download operation URL:{}".format(url))
            return True

        file_name = self.get_file_name(data)
        path = ConfigurationEntry.get().get_download_path()

        yt = ytdlp.YTDLP(url, cwd=path)
        if not yt.download_audio(file_name):
            AppLogging.error("Could not download music: " + url + " " + title)
            return

        id3 = id3v2.Id3v2(file_name, data=data, cwd=path)
        id3.tag()

        elapsed_sec = self.get_time_diff()

        AppLogging.notify(
            "Downloading music done: {} {}. Time:{}".format(url, title, elapsed_sec)
        )

        return True

    def get_data(self, obj):
        title = ""
        author = None
        album = None

        url = obj.subject

        entries = LinkDataController.objects.filter(link=url)
        if entries.exists():
            entry = entries[0]
            title = entry.title
            author = entry.author
            album = entry.album

        data = {
            "author": str(author),
            "album": str(album),
            "title": str(title),
            "url": url,
        }

        return data

    def get_file_name(self, data):
        file_name = Path(str(data["title"]) + ".mp3")
        if data["album"]:
            file_name = Path(data["album"]) / file_name

        if data["author"]:
            file_name = Path(data["author"]) / file_name

        file_name = fix_path_for_os(str(file_name))

        return file_name


class LinkVideoDownloadJobHandler(BaseJobHandler):
    """!
    downloads entry video
    """

    def get_job():
        return BackgroundJob.JOB_LINK_DOWNLOAD_VIDEO

    def process(self, obj=None):
        c = Configuration.get_object()

        data = self.get_data(obj)

        url = data["url"]
        title = data["title"]
        author = data["author"]
        album = data["album"]

        if not UrlLocation(url).is_youtube():
            AppLogging.error("Unsupported download operation URL:{}".format(url))
            return True

        AppLogging.info("Downloading music: " + url + " " + title)

        file_name = self.get_file_name(data)
        path = ConfigurationEntry.get().get_download_path()

        yt = ytdlp.YTDLP(url, cwd=path)
        if not yt.download_video("file.mp4"):
            AppLogging.error("Could not download video: " + url + " " + title)
            return

        elapsed_sec = self.get_time_diff()
        AppLogging.notify(
            "Downloading video done: {} {}. Time:{}".format(url, title, elapsed_sec)
        )

        return True

    def get_data(self, obj):
        title = ""
        author = None
        album = None

        url = obj.subject

        entries = LinkDataController.objects.filter(link=url)
        if entries.exists():
            entry = entries[0]
            title = entry.title
            author = entry.author
            album = entry.album

        data = {
            "author": str(author),
            "album": str(album),
            "title": str(title),
            "url": url,
        }

        return data

    def get_file_name(self, data):
        file_name = Path(str(data["title"]) + ".mp3")
        if data["album"]:
            file_name = Path(data["album"]) / file_name

        if data["author"]:
            file_name = Path(data["author"]) / file_name

        file_name = fix_path_for_os(str(file_name))

        return file_name


class DownloadModelFileJobHandler(BaseJobHandler):
    """!
    downloads entry video
    """

    def get_job():
        return BackgroundJob.JOB_DOWNLOAD_FILE

    def process(self, obj=None):
        c = Configuration.get_object()
        if not c.config_entry.enable_file_support:
            # consume
            return True

        file_name = obj.subject
        p = UrlLocation(file_name)
        if not p.is_web_link():
            # consume
            return True

        ModelFilesBuilder().build(file_name)

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
        data = self.get_data_for_add(obj)
        self.add_link(data)

        return True

    def add_link(self, data):
        # Unpack if link service
        link = data["link"]
        if UrlLocation(link).is_link_service():
            h = UrlHandlerEx(link)
            if h.get_contents():
                # TODO we should use response
                #link = h.response.url
                data["link"] = link

        # Add the link
        b = EntryDataBuilder()
        b.link_data = data
        b.link = link
        b.source_is_auto = True

        if not UrlLocation(link).is_web_link():
            AppLogging.error("Someone posted wrong link:{}".format(link))
            return

        entry = b.build_from_link()

        if not entry:
            # TODO send notification?
            LinkDatabase.info("Could not add link: {}".format(data["link"]))
            return True

        current_time = DateUtils.get_datetime_now_utc()

        # if this is a new entry, then tag it
        if entry.date_published:
            if entry.date_published >= current_time:
                if "tags" in data:
                    UserTags.set_tags(entry, tag=data["tags"], user=data["user_object"])

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
        item = obj.subject

        wb = WaybackMachine()
        if wb.is_saved(item):
            wb.save(item)

        return True


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
        AppLogging.notify("Received request to import files")

        data = {}
        try:
            data = json.loads(obj.args)
        except ValueError:
            AppLogging.error("Cannot load JSON")
            return False

        username = ""
        if "username" in data:
            username = data["username"]

        path = ""
        if "path" in data:
            path = data["path"]

        if path == "":
            AppLogging.error("Improperly configured")
            return False

        if not Path(path).exists():
            AppLogging.error("Path does not exist: {}".format(path))
            return False

        user = None
        if username and username != "":
            users = User.objects.filter(username=username)
            if users.count() > 0:
                user = users[0]

        data["user"] = user

        AppLogging.notify(
            "Importing from {}".format(path), detail_text="{}".format(data)
        )
        importer = JsonImporter(path=path, user=user, import_settings=data)
        importer.import_all()

        AppLogging.notify("Importing from {} DONE".format(path))

        return True


class WriteDailyDataJobHandler(BaseJobHandler):
    """!
    Writes daily data to disk
    """

    def get_job():
        return BackgroundJob.JOB_WRITE_DAILY_DATA

    def process(self, obj=None):
        from .updatemgr import UpdateManager
        from .datawriter import DataWriter

        date_input = datetime.strptime(obj.subject, "%Y-%m-%d").date()

        mgr = UpdateManager(self._config)

        all_export_data = DataExport.objects.filter(
            export_data=DataExport.EXPORT_DAILY_DATA, enabled=True
        )

        for export_data in all_export_data:
            mgr.write(export_data, date_input.isoformat())

        return True


class WriteYearDataJobHandler(BaseJobHandler):
    """!
    Writes yearly data to disk
    """

    def get_job():
        return BackgroundJob.JOB_WRITE_YEAR_DATA

    def process(self, obj=None):
        from .updatemgr import UpdateManager

        c = Configuration.get_object()
        mgr = UpdateManager(c)

        all_export_data = DataExport.objects.filter(
            export_data=DataExport.EXPORT_DAILY_DATA, enabled=True
        )

        for export_data in all_export_data:
            mgr.write(export_data)

        return True


class WriteNoTimeDataJobHandler(BaseJobHandler):
    """!
    Writes yearly data to disk
    """

    def get_job():
        return BackgroundJob.JOB_WRITE_NOTIME_DATA

    def process(self, obj=None):
        from .updatemgr import UpdateManager

        c = Configuration.get_object()
        mgr = UpdateManager(c)

        all_export_data = DataExport.objects.filter(
            export_data=DataExport.EXPORT_NOTIME_DATA, enabled=True
        )

        for export_data in all_export_data:
            mgr.write(export_data)

        return True


class WriteTopicJobHandler(BaseJobHandler):
    """!
    Writes topic data to disk
    """

    def get_job():
        return BackgroundJob.JOB_WRITE_TOPIC_DATA

    def process(self, obj=None):
        from ..serializers.bookmarksexporter import BookmarksTopicExporter

        topic = obj.subject

        c = Configuration.get_object()
        exporter = BookmarksTopicExporter(c)
        exporter.export(topic)

        return True


class ExportDataJobHandler(BaseJobHandler):
    """!
    Exports data to repo
    """

    def get_job():
        return BackgroundJob.JOB_EXPORT_DATA

    def process(self, obj=None):
        from .updatemgr import UpdateManager

        export = self.get_export(obj)
        if not export:
            AppLogging.error("Export {} does not exist".format(obj.subject))
            return

        AppLogging.notify("Exporting data. Export:{}".format(obj.subject))

        update_mgr = UpdateManager(self._config)

        update_mgr.write_and_push(export)

        elapsed_sec = self.get_time_diff()
        AppLogging.notify(
            "Successfully pushed data to git. Export:{} Time:{}".format(
                obj.subject, elapsed_sec
            )
        )

        return True

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
        from .updatemgr import UpdateManager

        update_mgr = UpdateManager(self._config)

        all_export_data = DataExport.objects.filter(
            export_data=DataExport.EXPORT_YEAR_DATA, enabled=True
        )

        for export_data in all_export_data:
            update_mgr.write_and_push(export_data)

        elapsed_sec = self.get_time_diff()
        AppLogging.notify(
            "Successfully pushed data to git. Time:{}".format(elapsed_sec)
        )

        return True


class PushNoTimeDataToRepoJobHandler(BaseJobHandler):
    """!
    Pushes data to repo
    """

    def get_job():
        return BackgroundJob.JOB_PUSH_NOTIME_DATA_TO_REPO

    def process(self, obj=None):
        from .updatemgr import UpdateManager

        update_mgr = UpdateManager(self._config)

        all_export_data = DataExport.objects.filter(
            export_data=DataExport.EXPORT_NOTIME_DATA, enabled=True
        )

        for export_data in all_export_data:
            update_mgr.write_and_push(export_data)

        elapsed_sec = self.get_time_diff()
        AppLogging.notify(
            "Successfully pushed data to git. Time:{}".format(elapsed_sec)
        )

        return True


class PushDailyDataToRepoJobHandler(BaseJobHandler):
    """!
    Pushes data to repo
    """

    def get_job():
        return BackgroundJob.JOB_PUSH_DAILY_DATA_TO_REPO

    def process(self, obj=None):
        # TODO read date from string
        from .updatemgr import UpdateManager

        date_input = obj.subject

        if date_input == "":
            date_input = DateUtils.get_date_yesterday()
        else:
            date_input = datetime.strptime(date_input, "%Y-%m-%d").date()

        update_mgr = UpdateManager(self._config)

        all_export_data = DataExport.objects.filter(
            export_data=DataExport.EXPORT_NOTIME_DATA, enabled=True
        )

        for export_data in all_export_data:
            update_mgr.write_and_push(export_data, date_input)

        elapsed_sec = self.get_time_diff()
        AppLogging.notify(
            "Successfully pushed data to git. Time:{}".format(elapsed_sec)
        )

        return True


class InitializeJobHandler(BaseJobHandler):
    """!
    Pushes data to repo
    """

    def get_job():
        return BackgroundJob.JOB_INITIALIZE

    def process(self, obj=None):
        # TODO read year from string
        BlockEntryList.initialize()
        return True


class InitializeBlockListJobHandler(BaseJobHandler):
    """!
    Pushes data to repo
    """

    def get_job():
        return BackgroundJob.JOB_INITIALIZE_BLOCK_LIST

    def process(self, obj=None):
        # TODO read year from string
        list = obj.subject

        lists = BlockEntryList.objects.filter(url=list)

        if lists.exists():
            lists[0].update_implementation()
        return True


class CleanupJobHandler(BaseJobHandler):
    """!
    Pushes data to repo
    """

    def get_job():
        return BackgroundJob.JOB_CLEANUP

    def cleanup_all(args=None):
        BackgroundJobController.create_single_job(
            BackgroundJob.JOB_CLEANUP, subject="LinkDataController", args=args
        )
        BackgroundJobController.create_single_job(
            BackgroundJob.JOB_CLEANUP, subject="SourceDataController", args=args
        )
        BackgroundJobController.create_single_job(
            BackgroundJob.JOB_CLEANUP, subject="AppLogging", args=args
        )
        BackgroundJobController.create_single_job(
            BackgroundJob.JOB_CLEANUP, subject="DomainsController", args=args
        )
        BackgroundJobController.create_single_job(
            BackgroundJob.JOB_CLEANUP, subject="KeyWords", args=args
        )
        BackgroundJobController.create_single_job(
            BackgroundJob.JOB_CLEANUP, subject="UserConfig", args=args
        )
        BackgroundJobController.create_single_job(
            BackgroundJob.JOB_CLEANUP, subject="SourceExportHistory", args=args
        )
        BackgroundJobController.create_single_job(
            BackgroundJob.JOB_CLEANUP, subject="ModelFiles", args=args
        )
        BackgroundJobController.create_single_job(
            BackgroundJob.JOB_CLEANUP, subject="SystemOperation", args=args
        )
        BackgroundJobController.create_single_job(
            BackgroundJob.JOB_CLEANUP, subject="UserTags", args=args
        )
        BackgroundJobController.create_single_job(
            BackgroundJob.JOB_CLEANUP, subject="UserComments", args=args
        )
        BackgroundJobController.create_single_job(
            BackgroundJob.JOB_CLEANUP, subject="UserVotes", args=args
        )
        BackgroundJobController.create_single_job(
            BackgroundJob.JOB_CLEANUP, subject="UserBookmarks", args=args
        )
        BackgroundJobController.create_single_job(
            BackgroundJob.JOB_CLEANUP, subject="UserSearchHistory", args=args
        )
        BackgroundJobController.create_single_job(
            BackgroundJob.JOB_CLEANUP, subject="UserEntryTransitionHistory", args=args
        )
        BackgroundJobController.create_single_job(
            BackgroundJob.JOB_CLEANUP, subject="UserEntryVisitHistory", args=args
        )
        BackgroundJobController.create_single_job(
            BackgroundJob.JOB_CLEANUP, subject="Gateway", args=args
        )

    def process(self, obj=None):
        """
        Cleanup:
         subject - table name, or all
         args["verify"] = True - check consistency of data, full
        """
        table = obj.subject

        if table == "":
            CleanupJobHandler.cleanup_all(obj.args)
            return True

        status = False

        limit_s = 0
        cfg = {}
        if obj.args != "":
            try:
                cfg = json.loads(obj.args)
            except ValueError as E:
                pass
            except TypeError as E:
                pass

        AppLogging.notify("Cleaning up table {}".format(table))

        cfg["limit_s"] = limit_s

        if table == "all" or table == "LinkDataController":
            status = EntriesCleanupAndUpdate().cleanup(cfg)
        if table == "all" or table == "SourceDataController":
            SourceDataController.cleanup(cfg)
        if table == "all" or table == "AppLogging":
            AppLogging.cleanup(cfg)
        if table == "all" or table == "DomainsController":
            DomainsController.cleanup(cfg)
        if table == "all" or table == "KeyWords":
            KeyWords.cleanup(cfg)
        if table == "all" or table == "UserConfig":
            UserConfig.cleanup(cfg)
        if table == "all" or table == "SourceExportHistory":
            SourceExportHistory.cleanup(cfg)
        if table == "all" or table == "ModelFiles":
            ModelFiles.cleanup(cfg)
        if table == "all" or table == "SystemOperation":
            from .controllers import SystemOperationController
            from .threadprocessors import get_tasks
            SystemOperationController.cleanup(cfg, get_tasks())
        if table == "all" or table == "Gateway":
            Gateway.cleanup(cfg)

        self.user_tables_cleanup(cfg, obj)

        status = True

        elapsed_sec = self.get_time_diff()
        AppLogging.notify("Successfully cleaned database. Time:{}".format(elapsed_sec))
        return status

    def user_tables_cleanup(self, cfg, obj):
        table = obj.subject

        if table == "all" or table == "UserTags":
            UserTags.cleanup(cfg)
            CompactedTags.cleanup(cfg)
            UserCompactedTags.cleanup(cfg)
        if table == "all" or table == "UserComments":
            UserCommentsController.cleanup(cfg)
        if table == "all" or table == "UserVotes":
            UserVotes.cleanup(cfg)
        if table == "all" or table == "UserBookmarks":
            UserBookmarks.cleanup(cfg)
        if table == "all" or table == "UserSearchHistory":
            UserSearchHistory.cleanup(cfg)
        if table == "all" or table == "UserEntryTransitionHistory":
            UserEntryTransitionHistory.cleanup(cfg)
        if table == "all" or table == "UserEntryVisitHistory":
            UserEntryVisitHistory.cleanup(cfg)


class CheckDomainsJobHandler(BaseJobHandler):
    def get_job():
        return BackgroundJob.JOB_CHECK_DOMAINS

    def process(self, obj=None):
        DomainsController.update_all()

        return True


class LinkScanJobHandler(BaseJobHandler):
    def get_job():
        return BackgroundJob.JOB_LINK_SCAN

    def process(self, obj=None):
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

        p = UrlHandlerEx(link)
        contents = p.get_contents()

        if entry:
            scanner = EntryScanner(entry=entry, contents=contents)
            scanner.run()
        else:
            scanner = EntryScanner(url=link, contents=contents)
            scanner.run()

        return True


class MoveToArchiveJobHandler(BaseJobHandler):
    def get_job():
        return BackgroundJob.JOB_MOVE_TO_ARCHIVE

    def process(self, obj=None):
        LinkDataController.move_old_links_to_archive()

        return True


class RunRuleJobHandler(BaseJobHandler):
    def get_job():
        return BackgroundJob.JOB_RUN_RULE

    def process(self, obj=None):
        try:
            rule_id = int(obj.subject)
        except ValueError:
            AppLogging.error("Such rule does not exist")
            return True

        rules = EntryRules.objects.filter(id=rule_id)

        entries_all = LinkDataController.objects.all()
        p = Paginator(entries_all, 1000)
        for page in p.num_pages:
            page_obj = p.get_page(page_num)
            entries = entries_all[page_obj.start_index() - 1 : page_obj.end_index()]

            for rule in rules:
                if rule.is_blocked_by_rule(entry.link):
                    entry.delete()

        return True
