from datetime import datetime, timedelta
from django.contrib.auth.models import User
import logging

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
    GenericJobsProcessor,
    SourceJobsProcessor,
    LeftOverJobsProcessor,
    RefreshProcessor,
    CleanupJobHandler,
    LinkAddJobHandler,
    LinkScanJobHandler,
    WriteDailyDataJobHandler,
    ExportDataJobHandler,
    ProcessSourceJobHandler,
)

from .fakeinternet import FakeInternetTestCase


# Test individual handlers


class RefreshThreadHandlerTest(FakeInternetTestCase):
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
            user="user",
            password="password",
        )

        DataExport.objects.create(
            enabled=True,
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_YEAR_DATA,
            local_path="test",
            remote_path="test.git",
            user="user",
            password="password",
        )

        DataExport.objects.create(
            enabled=True,
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_NOTIME_DATA,
            local_path="test",
            remote_path="test.git",
            user="user",
            password="password",
        )

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
            BackgroundJobController.objects.filter(
                job=BackgroundJobController.JOB_PROCESS_SOURCE
            ).count(),
            1,
        )

        self.assertEqual(
            BackgroundJobController.objects.filter(
                job=BackgroundJobController.JOB_CLEANUP
            ).count(),
            1,
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
            BackgroundJobController.objects.filter(
                job=BackgroundJobController.JOB_CLEANUP
            ).count(),
            1,
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


class CleanJobHandlerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = self.get_user(
            username="test_username", password="testpassword", is_superuser=True
        )

    def prepare_data(self):
        # inserts old data, we will check if those will be removed
        conf = Configuration.get_object().config_entry
        conf.accept_domains = True
        conf.save()

        p = AppLogging.objects.create(info_text="info1", level=10, user="test")
        p.date = DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M")
        p.save()

        p = AppLogging.objects.create(info_text="info2", level=10, user="test")
        p.date = DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M")
        p.save()

        p = AppLogging.objects.create(info_text="info3", level=10, user="test")
        p.date = DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M")
        p.save()

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            export_to_cms=True,
        )
        LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=bookmarked",
            title="The first link",
            source=source_youtube,
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=nonbookmarked",
            title="The second link",
            source=source_youtube,
            bookmarked=False,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=permanent",
            title="The first link",
            source=source_youtube,
            permanent=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com",
            title="The first link",
            source=source_youtube,
            permanent=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        DomainsController.objects.create(
            protocol="https",
            domain="youtube.com",
        )
        datetime = KeyWords.get_keywords_date_limit() - timedelta(days=1)
        keyword = KeyWords.objects.create(keyword="test")
        keyword.date_published = datetime
        keyword.save()

    def test_cleanup_job(self):
        self.prepare_data()

        handler = CleanupJobHandler()
        handler.process()

        # cleanup of links, domains may trigger creating new entries, which may
        # trigger unwanted dependencies

        persistent_objects = AppLogging.objects.filter(level=int(logging.ERROR))

        for persistent_object in persistent_objects:
            print("Persisten object info:{}".format(persistent_object.info_text))

        self.assertEqual(persistent_objects.count(), 0)
        self.assertEqual(KeyWords.objects.all().count(), 0)

        for domain in DomainsController.objects.all():
            print("Domain: {}".format(domain.domain))

        self.assertEqual(DomainsController.objects.all().count(), 0)

    def test_cleanup_job_no_store_domains(self):
        self.prepare_data()

        conf = Configuration.get_object().config_entry
        conf.accept_domains = False
        conf.save()

        handler = CleanupJobHandler()
        handler.process()

        persistent_objects = AppLogging.objects.filter(level=int(logging.ERROR))

        for persistent_object in persistent_objects:
            print("Persisten object info:{}".format(persistent_object.info_text))

        self.assertEqual(persistent_objects.count(), 0)
        self.assertEqual(KeyWords.objects.all().count(), 0)

        self.assertEqual(DomainsController.objects.all().count(), 0)


class AddJobHandlerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = self.get_user(
            username="test_username", password="testpassword", is_superuser=True
        )

    def test_add_link(self):
        conf = Configuration.get_object().config_entry
        conf.accept_domains = True
        conf.save()

        LinkDataController.objects.all().delete()
        DomainsController.objects.all().delete()

        ob = BackgroundJobController.link_add("https://manually-added-link.com")

        handler = LinkAddJobHandler()
        handler.process(ob)

        persistent_objects = AppLogging.objects.filter(level=int(logging.ERROR))

        for persistent_object in persistent_objects:
            print("Persisten object info:{}".format(persistent_object.info_text))

        self.assertEqual(persistent_objects.count(), 0)
        self.assertEqual(LinkDataController.objects.all().count(), 1)
        self.assertEqual(DomainsController.objects.all().count(), 1)

    def test_add_link_with_props(self):
        conf = Configuration.get_object().config_entry
        conf.accept_domains = True
        conf.save()

        LinkDataController.objects.all().delete()
        DomainsController.objects.all().delete()

        ob = BackgroundJobController.link_add(
            "https://manually-added-link.com", tag="demoscene"
        )

        handler = LinkAddJobHandler()
        handler.process(ob)

        persistent_objects = AppLogging.objects.filter(level=int(logging.ERROR))

        for persistent_object in persistent_objects:
            print("Persisten object info:{}".format(persistent_object.info))

        self.assertEqual(persistent_objects.count(), 0)
        self.assertEqual(LinkDataController.objects.all().count(), 1)
        self.assertEqual(DomainsController.objects.all().count(), 1)


class ScanLinkJobHandlerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = self.get_user(
            username="test_username", password="testpassword", is_superuser=True
        )

    def test_scan_link(self):
        conf = Configuration.get_object().config_entry
        conf.accept_domains = True
        conf.save()

        LinkDataController.objects.all().delete()
        DomainsController.objects.all().delete()

        ob = BackgroundJobController.link_scan("https://manually-added-link.com")

        handler = LinkScanJobHandler()
        handler.process(ob)

        persistent_objects = AppLogging.objects.filter(level=int(logging.ERROR))

        for persistent_object in persistent_objects:
            print("Persisten object info:{}".format(persistent_object.info_text))

        self.assertEqual(persistent_objects.count(), 0)

        jobs = BackgroundJobController.objects.all()
        for job in jobs:
            print("Job:{} {}".format(job.job, job.subject))

        self.assertEqual(jobs.count(), 1)


class ProcessSourceHandlerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = self.get_user(
            username="test_username", password="testpassword", is_superuser=True
        )

    def test_process__source_unknown(self):
        LinkDataController.objects.all().delete()
        DomainsController.objects.all().delete()
        SourceDataController.objects.all().delete()

        ob = BackgroundJobController.objects.create(
            job=BackgroundJob.JOB_PROCESS_SOURCE,
            subject="https://manually-added-link.com",
        )

        handler = ProcessSourceJobHandler()
        # call tested function
        result = handler.process(ob)

        self.print_errors()

        self.assertEqual(result, False)

        ob.refresh_from_db()

        jobs = BackgroundJobController.objects.all()
        self.assertEqual(jobs.count(), 1)
        job = jobs[0]
        self.assertEqual(job.enabled, False)

    def test_process__source_known(self):
        LinkDataController.objects.all().delete()
        DomainsController.objects.all().delete()
        SourceDataController.objects.all().delete()
        BackgroundJobController.objects.all().delete()

        source = SourceDataController.objects.create(
            url="https://www.youtube.com/feeds/channel=samtime"
        )

        ob = BackgroundJobController.objects.create(
            job=BackgroundJob.JOB_PROCESS_SOURCE,
            subject=str(source.id),
        )

        handler = ProcessSourceJobHandler()
        # call tested function
        result = handler.process(ob)

        persistent_objects = AppLogging.objects.filter(level=int(logging.ERROR))
        for persistent_object in persistent_objects:
            print("AppLogging object info:{}".format(persistent_object.info_text))

        self.assertEqual(persistent_objects.count(), 0)

        self.assertEqual(result, True)

        subjects = BackgroundJobController.objects.values_list("job", flat=True)

        self.assertEqual(len(subjects), 2)
        # still process source is present
        self.assertTrue("process-source" in subjects)
        # add link job odysee
        self.assertTrue("link-add" in subjects)


class WriteDailyDataJobHandlerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = self.get_user(
            username="test_username", password="testpassword", is_superuser=True
        )
        self.create_exports()

    def create_exports(self):
        DataExport.objects.create(
            enabled=True,
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_DAILY_DATA,
            local_path="test",
            remote_path="test.git",
            user="user",
            password="password",
        )

    def test_process(self):
        LinkDataController.objects.all().delete()
        DomainsController.objects.all().delete()
        SourceDataController.objects.all().delete()

        ob = BackgroundJobController.objects.create(
            job=BackgroundJob.JOB_WRITE_DAILY_DATA,
            subject="2024-06-23",
        )

        LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=12345",
            date_published=DateUtils.from_string("2024-06-23T11:35:31Z"),
        )

        handler = WriteDailyDataJobHandler()
        handler.set_config(Configuration.get_object())
        # call tested function
        result = handler.process(ob)

        self.print_errors()

        self.assertEqual(result, True)


class ExportDataJobHandlerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = self.get_user(
            username="test_username", password="testpassword", is_superuser=True
        )
        self.create_exports()

    def create_exports(self):
        self.export_obj = DataExport.objects.create(
            enabled=True,
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_DAILY_DATA,
            local_path="test",
            remote_path="test.git",
            user="user",
            password="password",
        )
        self.export_id = self.export_obj.id

    def test_process(self):
        LinkDataController.objects.all().delete()
        DomainsController.objects.all().delete()
        SourceDataController.objects.all().delete()

        ob = BackgroundJobController.objects.create(
            job=BackgroundJob.JOB_EXPORT_DATA, subject=str(self.export_id)
        )

        LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=12345",
            date_published=DateUtils.from_string("2024-06-23T11:35:31Z"),
        )

        handler = ExportDataJobHandler()
        handler.set_config(Configuration.get_object())

        # call tested function
        result = handler.process(ob)

        self.print_errors()

        self.assertEqual(result, True)


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


# test processors


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
        from ..controllers.backgroundjob import BackgroundJobController

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

    def test_get_handler_and_object_link_save_handler(self):
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

        self.assertEqual(BackgroundJobController.get_number_of_jobs(), 2)

        jobs = BackgroundJobController.objects.filter(
            job=BackgroundJobController.JOB_LINK_ADD
        )
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

    def test_process_job(self):
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

        mgr = LeftOverJobsProcessor()

        jobs = mgr.get_supported_jobs()

        self.assertTrue(BackgroundJob.JOB_PROCESS_SOURCE not in jobs)
