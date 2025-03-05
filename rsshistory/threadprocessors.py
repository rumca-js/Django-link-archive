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
    BackgroundJobHistory,
    SourceExportHistory,
    DataExport,
    ConfigurationEntry,
)
from .pluginsources.sourcecontrollerbuilder import SourceControllerBuilder
from .controllers import (
    BackgroundJobController,
    SourceDataController,
    EntriesUpdater,
    SystemOperationController,
)
from .threadhandlers import (
    InitializeJobHandler,
    InitializeBlockListJobHandler,
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
    SourceAddJobHandler,
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
    RunRuleJobHandler,
)
from .configuration import Configuration


class CeleryTaskInterface(object):
    def run(self):
        raise NotImplementedError("Not implemented")

    def get_name(self):
        return self.__class__.__name__


class RefreshProcessor(CeleryTaskInterface):
    """!
    One of the most important tasks.
    It checks what needs to be done, and produces 'new' tasks'.

    @note This handler should only do limited amount of work.
    Mostly it should only add background jobs, and nothing more!
    """

    def __init__(self, tasks_info = None):
        self.tasks_info = tasks_info

    def run(self):
        c = Configuration.get_object()

        config = c.config_entry
        if config.block_job_queue:
            return

        systemcontroller = SystemOperationController()
        systemcontroller.refresh(self.get_name())

        if not systemcontroller.is_internet_ok():
            AppLogging.error("Internet is not OK")
            return

        if systemcontroller.is_remote_server_down():
            AppLogging.error("Remote server is down")
            return

        self.check_sources()

        for export in DataExport.objects.filter(enabled=True):
            if SourceExportHistory.is_update_required(export):
                self.do_update(export)
                SourceExportHistory.confirm(export)

        if systemcontroller.is_time_to_cleanup():
            BackgroundJobHistory.mark_done(job = BackgroundJob.JOB_CLEANUP, subject="")

            CleanupJobHandler.cleanup_all()

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

        if conf.enable_source_archiving:
            sources = SourceDataController.objects.filter(enabled=True)
            for source in sources:
                BackgroundJobController.link_save(source.url)

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

        if number_of_entries > 0:
            current_num_of_jobs = (
                BackgroundJobController.get_number_of_update_reset_jobs()
            )

            if current_num_of_jobs >= max_number_of_update_entries:
                return

            jobs_to_add = max_number_of_update_entries - current_num_of_jobs
            jobs_to_add = min(jobs_to_add, number_of_entries)

            for index in range(jobs_to_add):
                BackgroundJobController.entry_update_data(entries[index])

    def get_supported_jobs(self):
        return []


class GenericJobsProcessor(CeleryTaskInterface):
    """!
    @note Uses handler priority when processing jobs.
    """

    def __init__(self, timeout_s=60 * 10, tasks_info = None):
        """
        Default timeout is 10 minutes
        """
        self.timeout_s = timeout_s
        self.start_processing_time = None
        self.tasks_info = tasks_info

    def get_handlers(self):
        """
        @returns available handlers. Order is important
        """
        return [
            # fmt: off
            InitializeJobHandler,
            InitializeBlockListJobHandler,
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
            SourceAddJobHandler,
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
            RunRuleJobHandler,
            # fmt: on
        ]

    def run(self):
        self.start_processing_time = DateUtils.get_datetime_now_utc()

        c = Configuration.get_object()

        config = c.config_entry
        if config.block_job_queue:
            return

        systemcontroller = SystemOperationController()
        systemcontroller.refresh(self.get_name())

        if not systemcontroller.is_internet_ok():
            AppLogging.error("Internet is not OK")
            return

        if systemcontroller.is_remote_server_down():
            AppLogging.error("Remote server is down")
            return

        index = 0

        while True:
            should_stop = self.run_one_loop()
            if should_stop:
                break

            index += 1

            if index > 2000:
                AppLogging.error("GenericJobsProcessor:run index overflow")
                return

    def run_one_job(self, job):
        self.start_processing_time = DateUtils.get_datetime_now_utc()

        c = Configuration.get_object()

        systemcontroller = SystemOperationController()
        systemcontroller.refresh(self.get_name())

        handler = self.get_job_handler(job)
        items = [job, handler]

        self.process_job(items)

    def run_one_loop(self):
        """
        return True, if processing should stop
        """
        items = self.get_handler_and_object()
        if len(items) == 0:
            return True

        try:
            self.process_job(items)

            elapsed_time = (
                DateUtils.get_datetime_now_utc() - self.start_processing_time
            ).total_seconds()
            if elapsed_time >= self.timeout_s:
                self.on_not_safe_exit(items)
                return True

        except KeyboardInterrupt:
            return True

        except Exception as E:
            """
            This is general exception handling - because we do not know what errors can jobs
            generate. We do not want to stop all jobs processing.

            We continue job processing
            """
            obj = items[0]
            if obj:
                try:
                    obj.refresh_from_db()
                except Exception as refresh_e:
                    AppLogging.exc(
                        refresh_e,
                        info_text="Failed to refresh object from DB for Job:{}, Subject:{}".format(
                            obj.job, obj.subject
                        ),
                    )
                    return True

                AppLogging.exc(
                    E,
                    info_text="Job:{}, Subject:{}".format(obj.job, obj.subject),
                )
                obj.on_error()
            else:
                AppLogging.exc(
                    E,
                    info_text="Exception",
                )

                return True

        return False

    def process_job(self, items):
        config = Configuration.get_object()

        obj = items[0]
        handler_class = items[1]
        handler = None
        deleted = False

        if handler_class:
            handler = handler_class(config)

            if obj:
                obj.task = self.get_name()
                obj.save()

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

    def get_supported_jobs(self):
        return []

    def get_handler_and_object(self):
        """
        TODO select should be based on priority
        """

        jobs = self.get_supported_jobs()

        query_conditions = Q(enabled=True)
        if len(jobs) > 0:
            jobs_conditions = Q()

            for ajob in jobs:
                jobs_conditions |= Q(job=ajob)

            query_conditions &= jobs_conditions

        objs = BackgroundJobController.objects.filter(query_conditions).order_by(
            "priority", "date_created"
        )
        if objs.exists():
            obj = objs.first()

            handler = self.get_job_handler(obj)
            return [obj, handler]
        return []

    def get_job_handler(self, obj):
        for handler_class in self.get_handlers():
            if handler_class.get_job() == obj.job:
                return handler_class

    def on_not_safe_exit(self, items):
        AppLogging.debug("Not safe exit, adjusting job priorities.")

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


class SourceJobsProcessor(GenericJobsProcessor):
    """
    Processes only source jobs
    """

    def get_supported_jobs(self):
        return [
            BackgroundJob.JOB_PROCESS_SOURCE,
        ]


class WriteJobsProcessor(GenericJobsProcessor):
    """
    Processes only write / export jobs
    """

    def get_supported_jobs(self):
        return [
            BackgroundJob.JOB_WRITE_DAILY_DATA,
            BackgroundJob.JOB_WRITE_TOPIC_DATA,
            BackgroundJob.JOB_WRITE_YEAR_DATA,
            BackgroundJob.JOB_WRITE_NOTIME_DATA,
            BackgroundJob.JOB_EXPORT_DATA,
        ]


class ImportJobsProcessor(GenericJobsProcessor):
    """
    Processes only import jobs
    """

    def get_supported_jobs(self):
        return [
            BackgroundJob.JOB_IMPORT_DAILY_DATA,
            BackgroundJob.JOB_IMPORT_BOOKMARKS,
            BackgroundJob.JOB_IMPORT_SOURCES,
            BackgroundJob.JOB_IMPORT_INSTANCE,
            BackgroundJob.JOB_IMPORT_FROM_FILES,
        ]


class LeftOverJobsProcessor(GenericJobsProcessor):
    """
    There can be many queues handling jobs.
    This processor handles jobs that are not handled by other queues
    """

    def __init__(self, tasks_info = None):
        super().__init__(tasks_info = tasks_info)

    def get_supported_jobs(self):
        jobs = []
        choices = BackgroundJobController.JOB_CHOICES

        for choice in choices:
            jobs.append(choice[0])

        for processor in self.get_processors():
            if processor.__name__ == LeftOverJobsProcessor.__name__:
                continue

            processor_object = processor()

            processor_jobs = processor_object.get_supported_jobs()
            for processor_job in processor_jobs:
                if processor_job in jobs:
                    jobs.remove(processor_job)

        return jobs

    def get_processors(self):
        """
        TODO remove hardcoded code
        """
        processors = []
        for task_info in self.tasks_info:
            if task_info[1] == "RefreshProcessor":
                processors.append(RefreshProcessor)
            if task_info[1] == "SourceJobsProcessor":
                processors.append(SourceJobsProcessor)
            if task_info[1] == "WriteJobsProcessor":
                processors.append(WriteJobsProcessor)
            if task_info[1] == "ImportJobsProcessor":
                processors.append(ImportJobsProcessor)
            if task_info[1] == "LeftOverJobsProcessor":
                processors.append(LeftOverJobsProcessor)

        return processors


class OneTaskProcessor(GenericJobsProcessor):
    """
    To be used by processing if there is only one task running.
    that captures all necessar data.
    """

    def __init__(self):
        super().__init__()

    def run(self):
        for processor in self.get_processors():
            processor_object = processor()
            processor_object.run()

        leftover_processor = LeftOverJobsProcessor()
        leftover_processor.run()


def get_tasks():
    """
    TODO replace with what is passed
    """
    tasks = [
        [300.0, RefreshProcessor],
        [60.0, SourceJobsProcessor],
        [60.0, WriteJobsProcessor],
        [60.0, ImportJobsProcessor],
        [60.0, LeftOverJobsProcessor],
    ]

    return tasks
