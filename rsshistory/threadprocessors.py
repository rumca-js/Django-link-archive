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
import os
import gc
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
    TruncateTableJobHandler,
    MoveToArchiveJobHandler,
    ProcessSourceJobHandler,
    LinkAddJobHandler,
    SourceAddJobHandler,
    LinkScanJobHandler,
    LinkResetDataJobHandler,
    LinkResetLocalDataJobHandler,
    LinkDownloadSocialData,
    LinkDownloadJobHandler,
    LinkMusicDownloadJobHandler,
    LinkVideoDownloadJobHandler,
    DownloadModelFileJobHandler,
    EntryUpdateData,
    LinkSaveJobHandler,
    CheckDomainsJobHandler,
    RunRuleJobHandler,
    RefreshJobHandler,
)
from .configuration import Configuration


class CeleryTaskInterface(object):
    def __init__(self):
        c = Configuration.get_object()
        self.start_processing_time = None
        self.start_memory = c.get_memory_usage()

    def run(self):
        raise NotImplementedError("Not implemented")

    def get_name(self):
        return self.__class__.__name__

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
            TruncateTableJobHandler,
            MoveToArchiveJobHandler,
            ProcessSourceJobHandler,
            LinkAddJobHandler,
            SourceAddJobHandler,
            LinkScanJobHandler,
            LinkResetDataJobHandler,
            LinkResetLocalDataJobHandler,
            LinkDownloadJobHandler,
            LinkDownloadSocialData,
            LinkMusicDownloadJobHandler,
            LinkVideoDownloadJobHandler,
            DownloadModelFileJobHandler,
            EntryUpdateData,
            LinkSaveJobHandler,
            CheckDomainsJobHandler,
            RunRuleJobHandler,
            # fmt: on
        ]

    def display_memory(self):
        c = Configuration.get_object()

        pid = os.getpid()

        memory = c.get_memory_usage()
        resident = memory.rss / (1024 * 1024)
        virtual = memory.vms / (1024 * 1024)

        AppLogging.debug(
            "{}: Starting. Pid:{} Memory:{}/{} MB".format(
                self.get_name(), pid, resident, virtual
            )
        )

    def display_memory_diff(self):
        c = Configuration.get_object()

        pid = os.getpid()

        memory = c.get_memory_usage()

        resident = memory.rss / (1024 * 1024)
        virtual = memory.vms / (1024 * 1024)

        resident_diff = memory.rss - self.start_memory.rss
        virtual_diff = memory.vms - self.start_memory.vms

        name = self.get_name()

        if resident_diff > 0:
            AppLogging.warning(f"{name}: More memory resident memory {resident_diff}")
        if virtual_diff > 0:
            AppLogging.warning(f"{name}: More memory virtual memory {virtual_diff}")

    def get_handler_and_object(self):
        """
        TODO select should be based on priority
        """

        jobs = self.get_supported_jobs()
        if len(jobs) == 0:
            return []

        query_conditions = Q(enabled=True)
        if len(jobs) > 0:
            jobs_conditions = Q()

            for ajob in jobs:
                jobs_conditions |= Q(job=ajob)

            query_conditions &= jobs_conditions

        # order is in meta
        objs = BackgroundJobController.objects.filter(query_conditions)
        if objs.exists():
            obj = objs.first()

            handler = self.get_job_handler(obj)
            return [obj, handler]
        return []

    def get_job_handler(self, obj):
        for handler_class in self.get_handlers():
            if handler_class.get_job() == obj.job:
                return handler_class

    def get_supported_jobs(self):
        return []


class RefreshProcessor(CeleryTaskInterface):
    """!
    One of the most important tasks.
    It checks what needs to be done, and produces 'new' tasks'.

    @note This handler should only do limited amount of work.
    Mostly it should only add background jobs, and nothing more!
    """

    def __init__(self, tasks_info=None):
        super().__init__()
        self.tasks_info = tasks_info

    def run(self):
        self.run_one_job()

    def is_more_jobs(self):
        return False

    def run_one_job(self):
        c = Configuration.get_object()

        if c.is_memory_limit_reached():
            gc.collect()

            AppLogging.error(
                "{}: Memory limit reached at start, leaving".format(self.get_name())
            )
            return

        config = c.config_entry
        if config.block_job_queue:
            AppLogging.debug("{}: Job queue is locked".format(self.get_name()))
            return

        systemcontroller = SystemOperationController()
        systemcontroller.refresh(self.get_name())

        if systemcontroller.is_remote_server_down():
            return

        if not systemcontroller.is_internet_ok():
            return

        config = Configuration.get_object()

        handler = RefreshJobHandler(config)

        BackgroundJobHistory.mark_done(job_name=RefreshJobHandler.get_job(), subject="")
        handler.process()

        #self.display_memory_diff()
        gc.collect()
        self.display_memory_diff()

    def get_supported_jobs(self):
        return [BackgroundJob.JOB_REFRESH]


class GenericJobsProcessor(CeleryTaskInterface):
    """!
    @note Uses handler priority when processing jobs.
    """

    def __init__(self, timeout_s=60 * 1, tasks_info=None):
        """ """
        super().__init__()
        self.timeout_s = timeout_s
        self.tasks_info = tasks_info

    def run(self):
        if not self.perform_run_checks():
            return

        # AppLogging.debug("{}: Running jobs".format(self.get_name()))
        self.start_processing_time = DateUtils.get_datetime_now_utc()

        index = 0

        while True:
            should_stop = self.run_one_job()
            if should_stop:
                break

            if c.is_memory_limit_reached():
                AppLogging.error("{}: Memory limit reached".format(self.get_name()))
                return

            index += 1

            if index > 2000:
                AppLogging.error("{}:run index overflow".format(self.get_name()))
                return

    def perform_run_checks(self):
        c = Configuration.get_object()

        if c.is_memory_limit_reached():
            AppLogging.error(
                "{}: Memory limit reached at start, leaving".format(self.get_name())
            )
            return False

        config = c.config_entry
        if config.block_job_queue:
            AppLogging.debug("{}: Job queue is locked".format(self.get_name()))
            return False

        systemcontroller = SystemOperationController()
        systemcontroller.refresh(self.get_name())

        if not systemcontroller.is_internet_ok():
            AppLogging.debug("{}: Internet is not OK".format(self.get_name()))
            return False

        if systemcontroller.is_remote_server_down():
            AppLogging.debug("{}: Remote server is down".format(self.get_name()))
            return False

        return True

    def run_one_job_body(self, job):
        self.start_processing_time = DateUtils.get_datetime_now_utc()

        c = Configuration.get_object()

        systemcontroller = SystemOperationController()
        systemcontroller.refresh(self.get_name())

        handler = self.get_job_handler(job)
        items = [job, handler]

        self.process_job(items)

    def is_more_jobs(self):
        if not self.perform_run_checks():
            return False

        items = self.get_handler_and_object()
        if len(items) == 0:
            # AppLogging.debug("{}: No jobs".format(self.get_name()))
            return False

        return True

    def run_one_job(self):
        """
        return True, if processing should stop
        """
        if not self.perform_run_checks():
            return False

        items = self.get_handler_and_object()
        if len(items) == 0:
            #AppLogging.debug("{}: No jobs".format(self.get_name()))
            return False

        try:
            self.process_job(items)
            self.display_memory_diff()

        except KeyboardInterrupt:
            AppLogging.debug("{}: Keyboard interrupt".format(self.get_name()))
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
                AppLogging.debug("{} object exception".format(self.get_name()))

                return True

        return False

    def process_job(self, items):
        config = Configuration.get_object()

        obj = items[0]
        handler_class = items[1]
        handler = None
        deleted = False

        AppLogging.debug("{}: Processing job {}".format(self.get_name(), str(obj)))

        if handler_class:
            handler = handler_class(config)

            if obj:
                obj.task = self.get_name()
                obj.save()

            if handler:
                BackgroundJobHistory.mark_job_done(obj)
                if handler.process(obj):
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

        # order is in meta
        objs = BackgroundJobController.objects.filter(query_conditions)
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


class SystemJobsProcessor(GenericJobsProcessor):
    """
    Jobs that should be working without hiccup
    """

    def get_supported_jobs(self):
        return [
            BackgroundJob.JOB_CLEANUP,
            BackgroundJob.JOB_TRUNCATE_TABLE,
            BackgroundJob.JOB_LINK_RESET_LOCAL_DATA,
        ]


class UpdateJobsProcessor(GenericJobsProcessor):
    """
    Jobs that should be working without hiccup
    """

    def get_supported_jobs(self):
        return [
            BackgroundJob.JOB_LINK_UPDATE_DATA,
        ]


class BlockJobsProcessor(GenericJobsProcessor):
    """
    Jobs that should be working without hiccup
    """

    def get_supported_jobs(self):
        return [
            BackgroundJob.JOB_INITIALIZE_BLOCK_LIST,
        ]


class LeftOverJobsProcessor(GenericJobsProcessor):
    """
    There can be many queues handling jobs.
    This processor handles jobs that are not handled by other queues
    If too many jobs are here, they might starve other things
    """

    def __init__(self, tasks_info=None):
        super().__init__(tasks_info=tasks_info)

    def get_supported_jobs(self):
        jobs = []

        if not self.tasks_info:
            AppLogging.error("Task info not yet ready")
            return

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

        if len(jobs) == 0:
            AppLogging.error("Leftover processor does not have any jobs")
            return

        return jobs

    def get_processors(self):
        """
        TODO remove hardcoded code
        """
        processors = []
        for task_info in self.tasks_info:
            processor = processor_from_id(task_info[1])

            if processor:
                processors.append(processor)

        return processors


def processor_from_id(processor_id):
    if processor_id == "RefreshProcessor":
        return RefreshProcessor
    elif processor_id == "SourceJobsProcessor":
        return SourceJobsProcessor
    elif processor_id == "WriteJobsProcessor":
        return WriteJobsProcessor
    elif processor_id == "ImportJobsProcessor":
        return ImportJobsProcessor
    elif processor_id == "SystemJobsProcessor":
        return SystemJobsProcessor
    elif processor_id == "LeftOverJobsProcessor":
        return LeftOverJobsProcessor
    elif processor_id == "UpdateJobsProcessor":
        return UpdateJobsProcessor
    elif processor_id == "BlockJobsProcessor":
        return BlockJobsProcessor


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
