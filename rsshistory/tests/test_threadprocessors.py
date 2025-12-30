from datetime import datetime, timedelta
from django.contrib.auth.models import User
import logging
import json

from utils.dateutils import DateUtils

from ..controllers import (
    BackgroundJobController,
    LinkDataController,
    SourceDataController,
    DomainsController,
)
from ..models import (
    BackgroundJob,
    AppLogging,
    DataExport,
    SourceExportHistory,
    KeyWords,
    SystemOperation,
)
from ..configuration import Configuration
from ..threadhandlers import (
    CleanupJobHandler,
    LinkAddJobHandler,
    LinkScanJobHandler,
    WriteDailyDataJobHandler,
    ExportDataJobHandler,
    ProcessSourceJobHandler,
)
from ..threadprocessors import (
    GenericJobsProcessor,
    SourceJobsProcessor,
    LeftOverJobsProcessor,
    RefreshProcessor,
    SystemJobsProcessor,
)

from .fakeinternet import FakeInternetTestCase


class RefreshProcessorTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            export_to_cms=True,
        )

        BackgroundJobController.objects.all().delete()
        SourceExportHistory.objects.all().delete()

        self.user = self.get_user(
            username="test_username", password="testpassword", is_superuser=True
        )

    def create_exports(self):
        DataExport.objects.create(
            enabled=True,
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_DAILY_DATA,
            local_path="test",
            remote_path="test.git",
        )

        DataExport.objects.create(
            enabled=True,
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_YEAR_DATA,
            local_path="test",
            remote_path="test.git",
        )

        DataExport.objects.create(
            enabled=True,
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_NOTIME_DATA,
            local_path="test",
            remote_path="test.git",
        )

    def test_get_name(self):
        handler = RefreshProcessor()

        self.assertEqual(handler.get_name(), "RefreshProcessor")

    def test_refresh__process_no_exports(self):
        DataExport.objects.all().delete()
        SourceExportHistory.objects.all().delete()
        self.create_exports()

        handler = RefreshProcessor()
        # call tested function
        handler.run()

        persistent_objects = AppLogging.objects.filter(level=int(logging.ERROR))

        for persistent_object in persistent_objects:
            print("Persisten object info:{}".format(persistent_object.info))

        self.assertEqual(persistent_objects.count(), 0)

        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(
                BackgroundJobController.JOB_PROCESS_SOURCE
            ),
            1,
        )

        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(
                BackgroundJobController.JOB_CLEANUP
            ),
            19,
        )

        self.assertEqual(SourceExportHistory.objects.all().count(), 3)

    def test_refresh__process_with_exports(self):
        DataExport.objects.all().delete()
        SourceExportHistory.objects.all().delete()
        self.create_exports()

        handler = RefreshProcessor()
        # call tested function
        handler.run()

        self.assertEqual(
            BackgroundJobController.objects.filter(
                job=BackgroundJobController.JOB_PROCESS_SOURCE
            ).count(),
            1,
        )

        export_jobs = BackgroundJobController.objects.filter(
            job=BackgroundJobController.JOB_EXPORT_DATA
        )

        self.assertEqual(export_jobs.count(), 3)

        pks = export_jobs.values_list("subject")
        # TODO check if export id is in pks

        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(
                BackgroundJobController.JOB_CLEANUP
            ),
            20,
        )

    def test_refresh__adds_update_entry_job(self):
        DataExport.objects.all().delete()
        SourceExportHistory.objects.all().delete()

        LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=12345",
        )

        handler = RefreshProcessor()
        # call tested function
        handler.run()

        persistent_objects = AppLogging.objects.filter(level=int(logging.ERROR))

        for persistent_object in persistent_objects:
            print("Persisten object info:{}".format(persistent_object.info))

        self.assertEqual(persistent_objects.count(), 0)

        self.assertEqual(
            BackgroundJobController.objects.filter(
                job=BackgroundJobController.JOB_LINK_UPDATE_DATA
            ).count(),
            1,
        )

    def test_refresh__adds_export_all(self):
        DataExport.objects.all().delete()
        SourceExportHistory.objects.all().delete()
        self.create_exports()

        handler = RefreshProcessor()
        # call tested function
        handler.run()

        persistent_objects = AppLogging.objects.filter(level=int(logging.ERROR))

        for persistent_object in persistent_objects:
            print("Persisten object info:{}".format(persistent_object.info))

        self.assertEqual(persistent_objects.count(), 0)

        self.assertEqual(
            BackgroundJobController.objects.filter(
                job=BackgroundJobController.JOB_EXPORT_DATA
            ).count(),
            3,
        )

        export_histories = SourceExportHistory.objects.all()
        self.assertEqual(export_histories.count(), 3)

    def test_refresh__adds_export_not_failed(self):
        DataExport.objects.all().delete()
        SourceExportHistory.objects.all().delete()
        self.create_exports()

        for data_export in DataExport.objects.all():
            data_export.enabled = False
            data_export.save()

        handler = RefreshProcessor()
        # call tested function
        handler.run()

        persistent_objects = AppLogging.objects.filter(level=int(logging.ERROR))

        for persistent_object in persistent_objects:
            print("Persisten object info:{}".format(persistent_object.info))

        self.assertEqual(persistent_objects.count(), 0)

        self.assertEqual(
            BackgroundJobController.objects.filter(
                job=BackgroundJobController.JOB_EXPORT_DATA
            ).count(),
            0,
        )

        export_histories = SourceExportHistory.objects.all()
        self.assertEqual(export_histories.count(), 0)


class HandlerThatThrowsExceptionInProcess(object):
    def __init__(self, config=None):
        pass

    def process(self, obj=None):
        raise IOError("Though luck")


class GenericJobsProcessorError(GenericJobsProcessor):
    def __init__(self):
        super().__init__()

        self.obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_CLEANUP,
            enabled=True,
        )

    def get_handler_and_object(self):
        objs = BackgroundJobController.objects.filter(
            job=BackgroundJobController.JOB_CLEANUP,
            enabled=True,
        )
        if objs.exists():
            return [objs[0], HandlerThatThrowsExceptionInProcess]
        else:
            return []


class GenericJobsProcessorTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()
        self.setup_configuration()

        ob = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
        )
        LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=12345",
            source=ob,
        )

        self.user = self.get_user(
            username="test_username", password="testpassword", is_superuser=True
        )

    def test_job_consistency(self):
        mgr = GenericJobsProcessor()
        handlers = mgr.get_handlers()

        all_is_good = True

        for handler in handlers:
            found = False
            for choice in BackgroundJobController.JOB_CHOICES:
                if handler.get_job() == choice[0]:
                    found = True

            if not found:
                all_is_good = False

        self.assertTrue(all_is_good)

    def test_get_handler_and_object_invalid_job(self):
        bg_obj = BackgroundJobController.objects.create(
            job="invalid-job",
        )

        mgr = GenericJobsProcessor()
        # call tested function
        handler_obj, handler = mgr.get_handler_and_object()

        self.assertEqual(bg_obj, handler_obj)
        self.assertTrue(not handler)

    def test_get_handler_and_object_export_data_handler(self):
        bg_obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_EXPORT_DATA
        )

        mgr = GenericJobsProcessor()
        # call tested function
        handler_obj, handler = mgr.get_handler_and_object()

        self.assertEqual(bg_obj, handler_obj)
        self.assertEqual(handler.get_job(), BackgroundJobController.JOB_EXPORT_DATA)

    def test_get_handler_and_object_process_source_handler(self):
        bg_obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_PROCESS_SOURCE
        )

        mgr = GenericJobsProcessor()
        # call tested function
        handler_obj, handler = mgr.get_handler_and_object()

        self.assertEqual(bg_obj, handler_obj)
        self.assertEqual(handler.get_job(), BackgroundJobController.JOB_PROCESS_SOURCE)

    def test_get_handler_and_object_link_add_handler(self):
        bg_obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_LINK_ADD
        )

        mgr = GenericJobsProcessor()
        # call tested function
        handler_obj, handler = mgr.get_handler_and_object()

        self.assertEqual(bg_obj, handler_obj)
        self.assertEqual(handler.get_job(), BackgroundJobController.JOB_LINK_ADD)

    def test_get_handler_and_object_link_download_handler(self):
        bg_obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_LINK_DOWNLOAD
        )

        mgr = GenericJobsProcessor()
        # call tested function
        handler_obj, handler = mgr.get_handler_and_object()

        self.assertEqual(bg_obj, handler_obj)
        self.assertEqual(handler.get_job(), BackgroundJobController.JOB_LINK_DOWNLOAD)

    def test_get_handler_and_object_link_music_handler(self):
        bg_obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_LINK_DOWNLOAD_MUSIC
        )

        mgr = GenericJobsProcessor()
        # call tested function
        handler_obj, handler = mgr.get_handler_and_object()

        self.assertEqual(bg_obj, handler_obj)
        self.assertEqual(
            handler.get_job(), BackgroundJobController.JOB_LINK_DOWNLOAD_MUSIC
        )

    def test_get_handler_and_object_link_video_handler(self):
        bg_obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_LINK_DOWNLOAD_VIDEO
        )

        mgr = GenericJobsProcessor()
        # call tested function
        handler_obj, handler = mgr.get_handler_and_object()

        self.assertEqual(bg_obj, handler_obj)
        self.assertEqual(
            handler.get_job(), BackgroundJobController.JOB_LINK_DOWNLOAD_VIDEO
        )

    def test_get_handler_and_object__link_save_handler(self):
        bg_obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_LINK_SAVE
        )

        mgr = GenericJobsProcessor()
        # call tested function
        handler_obj, handler = mgr.get_handler_and_object()

        self.assertEqual(bg_obj, handler_obj)
        self.assertEqual(handler.get_job(), BackgroundJobController.JOB_LINK_SAVE)

    def test_get_handler_and_object_write_daily_data(self):
        bg_obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_WRITE_DAILY_DATA
        )

        mgr = GenericJobsProcessor()
        # call tested function
        handler_obj, handler = mgr.get_handler_and_object()

        self.assertEqual(bg_obj, handler_obj)
        self.assertEqual(
            handler.get_job(), BackgroundJobController.JOB_WRITE_DAILY_DATA
        )

    def test_get_handler_and_object_write_topic_handler(self):
        bg_obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_WRITE_TOPIC_DATA
        )

        mgr = GenericJobsProcessor()
        # call tested function
        handler_obj, handler = mgr.get_handler_and_object()

        self.assertEqual(bg_obj, handler_obj)
        self.assertEqual(
            handler.get_job(), BackgroundJobController.JOB_WRITE_TOPIC_DATA
        )

    def test_get_handler_and_object_import_sources(self):
        bg_obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_IMPORT_SOURCES
        )

        mgr = GenericJobsProcessor()
        # call tested function
        handler_obj, handler = mgr.get_handler_and_object()

        self.assertEqual(bg_obj, handler_obj)
        self.assertEqual(handler.get_job(), BackgroundJobController.JOB_IMPORT_SOURCES)

    def test_get_handler_and_object_import_bookmarks(self):
        bg_obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_IMPORT_BOOKMARKS
        )

        mgr = GenericJobsProcessor()
        # call tested function
        handler_obj, handler = mgr.get_handler_and_object()

        self.assertEqual(bg_obj, handler_obj)
        self.assertEqual(
            handler.get_job(), BackgroundJobController.JOB_IMPORT_BOOKMARKS
        )

    def test_get_handler_and_object_import_daily_data(self):
        bg_obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_IMPORT_DAILY_DATA
        )

        mgr = GenericJobsProcessor()
        # call tested function
        handler_obj, handler = mgr.get_handler_and_object()

        self.assertEqual(bg_obj, handler_obj)
        self.assertEqual(
            handler.get_job(), BackgroundJobController.JOB_IMPORT_DAILY_DATA
        )

    def test_get_handler_and_object_order(self):
        BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_PROCESS_SOURCE
        )

        BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_IMPORT_DAILY_DATA
        )

        # using order of 'appearance'

        mgr = GenericJobsProcessor()

        # call tested function
        handler_obj, handler = mgr.get_handler_and_object()

        self.assertTrue(handler_obj)
        self.assertEqual(handler_obj.job, BackgroundJobController.JOB_PROCESS_SOURCE)

        if handler_obj:
            handler_obj.delete()

        # call tested function
        handler_obj, handler = mgr.get_handler_and_object()

        self.assertTrue(handler_obj)
        self.assertEqual(handler_obj.job, BackgroundJobController.JOB_IMPORT_DAILY_DATA)

        if handler_obj:
            handler_obj.delete()

    def test_get_handler_and_object_job_disabled(self):
        BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_PROCESS_SOURCE, enabled=False
        )

        BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_IMPORT_DAILY_DATA
        )

        mgr = GenericJobsProcessor()

        # call tested function
        handler_obj, handler = mgr.get_handler_and_object()

        self.assertTrue(handler_obj)
        self.assertEqual(handler_obj.job, BackgroundJobController.JOB_IMPORT_DAILY_DATA)

        if handler_obj:
            handler_obj.delete()

        # call tested function
        items = mgr.get_handler_and_object()

        self.assertFalse(items)

    def test_run__adds_link(self):
        LinkDataController.objects.all().delete()

        BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_LINK_ADD,
            enabled=True,
            subject="https://youtube.com",
        )
        BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_LINK_ADD,
            enabled=True,
            subject="https://tiktok.com",
        )

        mgr = GenericJobsProcessor(timeout_s=60)

        # call tested function
        mgr.run()

        self.print_errors()

        self.assertEqual(BackgroundJobController.get_number_of_jobs(), 0)
        self.assertEqual(LinkDataController.objects.all().count(), 2)

    def test_run_timeout_changes_priority(self):
        LinkDataController.objects.all().delete()

        BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_CLEANUP,
            enabled=True,
        )
        BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_LINK_ADD,
            enabled=True,
            subject="https://youtube.com",
        )
        BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_LINK_ADD,
            enabled=True,
            subject="https://tiktok.com",
        )

        mgr = GenericJobsProcessor(timeout_s=0)

        # call tested function
        mgr.run()

        self.print_errors()

        jobs = BackgroundJobController.objects.filter(
            job=BackgroundJobController.JOB_LINK_ADD
        )
        self.assertTrue(jobs.exists())
        self.assertNotEqual(
            jobs[0].priority,
            BackgroundJobController.get_job_priority(
                BackgroundJobController.JOB_LINK_ADD
            ),
        )
        self.assertNotEqual(
            jobs[1].priority,
            BackgroundJobController.get_job_priority(
                BackgroundJobController.JOB_LINK_ADD
            ),
        )

        # 2 link add, 18 cleanups
        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(
                BackgroundJobController.JOB_CLEANUP
            ),
            19,
        )

        self.assertEqual(BackgroundJobController.get_number_of_jobs(), 19)

    def test_run__adds_system_operation(self):
        LinkDataController.objects.all().delete()

        BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_LINK_ADD,
            enabled=True,
            subject="https://youtube.com",
        )
        BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_LINK_ADD,
            enabled=True,
            subject="https://tiktok.com",
        )

        mgr = GenericJobsProcessor(timeout_s=60)

        # call tested function
        mgr.run()

        operations = SystemOperation.objects.all()
        self.assertTrue(operations.count(), 1)

    def test_process_job__exception(self):
        mgr = GenericJobsProcessor(timeout_s=0)

        obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_CLEANUP,
            enabled=True,
        )
        items = [obj, HandlerThatThrowsExceptionInProcess]

        mgr = GenericJobsProcessor(timeout_s=60)

        exception_raised = False
        try:
            # call tested function
            mgr.process_job(items)
        except IOError as E:
            exception_raised = True

        jobs = BackgroundJobController.objects.filter(
            job=BackgroundJobController.JOB_LINK_ADD
        )
        self.assertEqual(jobs.count(), 0)
        self.assertTrue(exception_raised)

    def test_process_job__noexception(self):
        mgr = GenericJobsProcessor(timeout_s=0)

        obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_CLEANUP,
            enabled=True,
        )
        items = [obj, CleanupJobHandler]

        mgr = GenericJobsProcessor(timeout_s=60)

        exception_raised = False
        try:
            # call tested function
            mgr.process_job(items)
        except IOError as E:
            exception_raised = True

        self.assertTrue(not exception_raised)

    def test_run(self):
        mgr = GenericJobsProcessorError()

        exception_raised = False
        try:
            # call tested function
            mgr.run()
        except IOError as E:
            exception_raised = True

        jobs = BackgroundJobController.objects.filter(
            job=BackgroundJobController.JOB_LINK_ADD
        )
        self.assertEqual(jobs.count(), 0)
        self.assertFalse(exception_raised)


class SourceJobsProcessorTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()
        self.setup_configuration()

        ob = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
        )
        LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=12345",
            source=ob,
        )

        self.user = self.get_user(
            username="test_username", password="testpassword", is_superuser=True
        )

    def test_get_handler__supported(self):
        bg_obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_PROCESS_SOURCE
        )

        mgr = SourceJobsProcessor()
        # call tested function
        items = mgr.get_handler_and_object()
        handler_obj = items[0]
        handler = items[1]

        self.assertEqual(handler_obj, bg_obj)
        self.assertEqual(handler.get_job(), BackgroundJobController.JOB_PROCESS_SOURCE)

    def test_get_handler__not_supported(self):
        bg_obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_EXPORT_DATA
        )

        mgr = SourceJobsProcessor()
        # call tested function
        items = mgr.get_handler_and_object()

        self.assertEqual(items, [])

    def test_get_handler_and_object_job_disabled(self):
        BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_PROCESS_SOURCE, enabled=False
        )

        BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_IMPORT_DAILY_DATA
        )

        mgr = SourceJobsProcessor()

        # call tested function
        items = mgr.get_handler_and_object()

        self.assertEqual(items, [])


class SystenJobProcessorTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()
        self.setup_configuration()

    def test_get_handler_and_object__cleanup_default(self):
        BackgroundJobController.objects.all().delete()

        self.obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_CLEANUP,
            enabled=True,
        )

        mgr = SystemJobsProcessor()
        # call tested function
        items = mgr.get_handler_and_object()
        handler_obj = items[0]
        handler = items[1]

        self.assertEqual(handler_obj, self.obj)
        self.assertEqual(handler.get_job(), BackgroundJobController.JOB_CLEANUP)

    def test_get_handler_and_object__cleanup_tablename(self):
        BackgroundJobController.objects.all().delete()

        self.obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_CLEANUP,
            subject="SourceDataController",
            enabled=True,
        )

        mgr = SystemJobsProcessor()
        # call tested function
        items = mgr.get_handler_and_object()
        handler_obj = items[0]
        handler = items[1]

        self.assertEqual(handler_obj, self.obj)
        self.assertEqual(handler.get_job(), BackgroundJobController.JOB_CLEANUP)

    def test_get_handler_and_object__truncate_default(self):
        BackgroundJobController.objects.all().delete()

        self.obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_TRUNCATE_TABLE,
            enabled=True,
        )

        mgr = SystemJobsProcessor()
        # call tested function
        items = mgr.get_handler_and_object()
        handler_obj = items[0]
        handler = items[1]

        self.assertEqual(handler_obj, self.obj)
        self.assertEqual(handler.get_job(), BackgroundJobController.JOB_TRUNCATE_TABLE)

    def test_get_handler_and_object__truncate_tablename(self):
        BackgroundJobController.objects.all().delete()

        self.obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_TRUNCATE_TABLE,
            subject="SourceDataController",
            enabled=True,
        )

        mgr = SystemJobsProcessor()
        # call tested function
        items = mgr.get_handler_and_object()
        handler_obj = items[0]
        handler = items[1]

        self.assertEqual(handler_obj, self.obj)
        self.assertEqual(handler.get_job(), BackgroundJobController.JOB_TRUNCATE_TABLE)


class LeftOverJobsProcessorTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()
        self.setup_configuration()

        ob = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
        )
        LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=12345",
            source=ob,
        )

        self.user = self.get_user(
            username="test_username", password="testpassword", is_superuser=True
        )

    def test_get_handler__supported(self):
        bg_obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_PROCESS_SOURCE
        )

        processors_list = [
            [300.0, "RefreshProcessor"],
            [60.0, "SourceJobsProcessor"],
            [60.0, "WriteJobsProcessor"],
            [60.0, "ImportJobsProcessor"],
            [60.0, "LeftOverJobsProcessor"],
        ]

        mgr = LeftOverJobsProcessor(processors_list=processors_list)

        jobs = mgr.get_supported_jobs()

        self.assertTrue(BackgroundJob.JOB_PROCESS_SOURCE not in jobs)
        self.assertTrue(BackgroundJob.JOB_LINK_ADD in jobs)

    def test_run__multiple_jobs(self):
        bg_obj = BackgroundJobController.link_add(url="https://linkedin.com")
        bg_obj = BackgroundJobController.link_add(url="https://test.com")

        self.assertEqual(BackgroundJobController.objects.all().count(), 2)

        processors_list = [
            [300.0, "RefreshProcessor"],
            [60.0, "SourceJobsProcessor"],
            [60.0, "WriteJobsProcessor"],
            [60.0, "ImportJobsProcessor"],
            [60.0, "LeftOverJobsProcessor"],
        ]

        mgr = LeftOverJobsProcessor(processors_list=processors_list)

        mgr.run()

        self.assertEqual(BackgroundJobController.objects.all().count(), 0)
        self.assertEqual(
            LinkDataController.objects.filter(link="https://linkedin.com").count(), 1
        )
        self.assertEqual(
            LinkDataController.objects.filter(link="https://test.com").count(), 1
        )


