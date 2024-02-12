from datetime import datetime, timedelta

from ..controllers import (
    BackgroundJobController,
    LinkDataController,
    SourceDataController,
    DomainsController,
)
from ..models import (
    BackgroundJob,
    PersistentInfo,
    DataExport,
    SourceExportHistory,
    KeyWords,
    DomainCategories,
    DomainSubCategories,
)
from ..configuration import Configuration
from ..threadhandlers import (
    HandlerManager,
    RefreshThreadHandler,
    CleanupJobHandler,
    LinkAddJobHandler,
    LinkScanJobHandler,
    ProcessSourceJobHandler,
)
from ..dateutils import DateUtils

from .fakeinternet import FakeInternetTestCase


class BackgroundJobControllerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        ob = SourceDataController.objects.create(
            url="https://youtube.com", title="YouTube", category="No", subcategory="No"
        )
        LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=12345",
            source_obj=ob,
        )

    def test_job_consistency(self):
        from ..controllers.backgroundjob import BackgroundJobController

        mgr = HandlerManager()
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

    def test_invalid_job(self):
        bg_obj = BackgroundJobController.objects.create(
            job="invalid-job",
        )

        mgr = HandlerManager()
        handler_obj, handler = mgr.get_handler_and_object()

        self.assertEqual(bg_obj, handler_obj)
        self.assertTrue(not handler)

    def test_push_to_repo_handler(self):
        bg_obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_PUSH_TO_REPO
        )

        mgr = HandlerManager()
        handler_obj, handler = mgr.get_handler_and_object()

        self.assertEqual(bg_obj, handler_obj)
        self.assertEqual(handler.get_job(), BackgroundJobController.JOB_PUSH_TO_REPO)

    def test_push_daily_data_to_repo_handler(self):
        bg_obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_PUSH_DAILY_DATA_TO_REPO
        )

        mgr = HandlerManager()
        handler_obj, handler = mgr.get_handler_and_object()

        self.assertEqual(bg_obj, handler_obj)
        self.assertEqual(
            handler.get_job(), BackgroundJobController.JOB_PUSH_DAILY_DATA_TO_REPO
        )

    def test_process_source_handler(self):
        bg_obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_PROCESS_SOURCE
        )

        mgr = HandlerManager()
        handler_obj, handler = mgr.get_handler_and_object()

        self.assertEqual(bg_obj, handler_obj)
        self.assertEqual(handler.get_job(), BackgroundJobController.JOB_PROCESS_SOURCE)

    def test_link_add_handler(self):
        bg_obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_LINK_ADD
        )

        mgr = HandlerManager()
        handler_obj, handler = mgr.get_handler_and_object()

        self.assertEqual(bg_obj, handler_obj)
        self.assertEqual(handler.get_job(), BackgroundJobController.JOB_LINK_ADD)

    def test_link_download_handler(self):
        bg_obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_LINK_DOWNLOAD
        )

        mgr = HandlerManager()
        handler_obj, handler = mgr.get_handler_and_object()

        self.assertEqual(bg_obj, handler_obj)
        self.assertEqual(handler.get_job(), BackgroundJobController.JOB_LINK_DOWNLOAD)

    def test_link_music_handler(self):
        bg_obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_LINK_DOWNLOAD_MUSIC
        )

        mgr = HandlerManager()
        handler_obj, handler = mgr.get_handler_and_object()

        self.assertEqual(bg_obj, handler_obj)
        self.assertEqual(
            handler.get_job(), BackgroundJobController.JOB_LINK_DOWNLOAD_MUSIC
        )

    def test_link_video_handler(self):
        bg_obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_LINK_DOWNLOAD_VIDEO
        )

        mgr = HandlerManager()
        handler_obj, handler = mgr.get_handler_and_object()

        self.assertEqual(bg_obj, handler_obj)
        self.assertEqual(
            handler.get_job(), BackgroundJobController.JOB_LINK_DOWNLOAD_VIDEO
        )

    def test_link_save_handler(self):
        bg_obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_LINK_SAVE
        )

        mgr = HandlerManager()
        handler_obj, handler = mgr.get_handler_and_object()

        self.assertEqual(bg_obj, handler_obj)
        self.assertEqual(handler.get_job(), BackgroundJobController.JOB_LINK_SAVE)

    def test_write_daily_data(self):
        bg_obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_WRITE_DAILY_DATA
        )

        mgr = HandlerManager()
        handler_obj, handler = mgr.get_handler_and_object()

        self.assertEqual(bg_obj, handler_obj)
        self.assertEqual(
            handler.get_job(), BackgroundJobController.JOB_WRITE_DAILY_DATA
        )

    def test_write_bookmarks_handler(self):
        bg_obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_WRITE_BOOKMARKS
        )

        mgr = HandlerManager()
        handler_obj, handler = mgr.get_handler_and_object()

        self.assertEqual(bg_obj, handler_obj)
        self.assertEqual(handler.get_job(), BackgroundJobController.JOB_WRITE_BOOKMARKS)

    def test_write_topic_handler(self):
        bg_obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_WRITE_TOPIC_DATA
        )

        mgr = HandlerManager()
        handler_obj, handler = mgr.get_handler_and_object()

        self.assertEqual(bg_obj, handler_obj)
        self.assertEqual(
            handler.get_job(), BackgroundJobController.JOB_WRITE_TOPIC_DATA
        )

    def test_import_sources(self):
        bg_obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_IMPORT_SOURCES
        )

        mgr = HandlerManager()
        handler_obj, handler = mgr.get_handler_and_object()

        self.assertEqual(bg_obj, handler_obj)
        self.assertEqual(handler.get_job(), BackgroundJobController.JOB_IMPORT_SOURCES)

    def test_import_bookmarks(self):
        bg_obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_IMPORT_BOOKMARKS
        )

        mgr = HandlerManager()
        handler_obj, handler = mgr.get_handler_and_object()

        self.assertEqual(bg_obj, handler_obj)
        self.assertEqual(
            handler.get_job(), BackgroundJobController.JOB_IMPORT_BOOKMARKS
        )

    def test_import_daily_data(self):
        bg_obj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_IMPORT_DAILY_DATA
        )

        mgr = HandlerManager()
        handler_obj, handler = mgr.get_handler_and_object()

        self.assertEqual(bg_obj, handler_obj)
        self.assertEqual(
            handler.get_job(), BackgroundJobController.JOB_IMPORT_DAILY_DATA
        )

    def test_order(self):
        BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_PROCESS_SOURCE
        )

        BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_IMPORT_DAILY_DATA
        )

        mgr = HandlerManager()

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


class RefreshThreadHandlerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )

        BackgroundJobController.objects.all().delete()
        SourceExportHistory.objects.all().delete()

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

    def test_process_no_exports(self):
        DataExport.objects.all().delete()

        handler = RefreshThreadHandler()
        handler.refresh()

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

        persistent_objects = PersistentInfo.objects.all()

        for persistent_object in persistent_objects:
            print("Persisten object info:{}".format(persistent_object.info))

        self.assertEqual(persistent_objects.count(), 0)
        self.assertEqual(SourceExportHistory.objects.all().count(), 1)

    def test_process_with_exports(self):
        self.create_exports()

        handler = RefreshThreadHandler()
        handler.refresh()

        self.assertEqual(
            BackgroundJobController.objects.filter(
                job=BackgroundJobController.JOB_PROCESS_SOURCE
            ).count(),
            1,
        )

        self.assertEqual(
            BackgroundJobController.objects.filter(
                job=BackgroundJobController.JOB_PUSH_DAILY_DATA_TO_REPO
            ).count(),
            1,
        )

        self.assertEqual(
            BackgroundJobController.objects.filter(
                job=BackgroundJobController.JOB_PUSH_YEAR_DATA_TO_REPO
            ).count(),
            1,
        )

        self.assertEqual(
            BackgroundJobController.objects.filter(
                job=BackgroundJobController.JOB_PUSH_NOTIME_DATA_TO_REPO
            ).count(),
            1,
        )

        self.assertEqual(
            BackgroundJobController.objects.filter(
                job=BackgroundJobController.JOB_CLEANUP
            ).count(),
            1,
        )


class CleanJobHandlerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def prepare_data(self):
        # inserts old data, we will check if those will be removed
        conf = Configuration.get_object().config_entry
        conf.auto_store_domain_info = True
        conf.save()

        p = PersistentInfo.objects.create(info="info1", level=10, user="test")
        p.date = DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M")
        p.save()

        p = PersistentInfo.objects.create(info="info2", level=10, user="test")
        p.date = DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M")
        p.save()

        p = PersistentInfo.objects.create(info="info3", level=10, user="test")
        p.date = DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M")
        p.save()

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )
        LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=bookmarked",
            title="The first link",
            source_obj=source_youtube,
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=nonbookmarked",
            title="The second link",
            source_obj=source_youtube,
            bookmarked=False,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=permanent",
            title="The first link",
            source_obj=source_youtube,
            permanent=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com",
            title="The first link",
            source_obj=source_youtube,
            permanent=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        DomainsController.objects.create(
            protocol="https",
            domain="youtube.com",
            category="testCategory",
            subcategory="testSubcategory",
        )
        DomainCategories.objects.all().delete()
        DomainSubCategories.objects.all().delete()

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

        persistent_objects = PersistentInfo.objects.all()

        for persistent_object in persistent_objects:
            print("Persisten object info:{}".format(persistent_object.info))

        self.assertEqual(persistent_objects.count(), 0)
        self.assertEqual(KeyWords.objects.all().count(), 0)

        self.assertEqual(DomainsController.objects.all().count(), 1)
        self.assertEqual(DomainCategories.objects.all().count(), 1)
        self.assertEqual(DomainSubCategories.objects.all().count(), 1)

    def test_cleanup_job_no_store_domains(self):
        self.prepare_data()

        conf = Configuration.get_object().config_entry
        conf.auto_store_domain_info = False
        conf.save()

        handler = CleanupJobHandler()
        handler.process()

        persistent_objects = PersistentInfo.objects.all()

        for persistent_object in persistent_objects:
            print("Persisten object info:{}".format(persistent_object.info))

        self.assertEqual(persistent_objects.count(), 0)
        self.assertEqual(KeyWords.objects.all().count(), 0)

        self.assertEqual(DomainsController.objects.all().count(), 0)
        self.assertEqual(DomainCategories.objects.all().count(), 0)
        self.assertEqual(DomainSubCategories.objects.all().count(), 0)


class AddJobHandlerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_add_link(self):
        conf = Configuration.get_object().config_entry
        conf.auto_store_domain_info = True
        conf.save()

        LinkDataController.objects.all().delete()
        DomainsController.objects.all().delete()

        ob = BackgroundJobController.link_add("https://manually-added-link.com")

        handler = LinkAddJobHandler()
        handler.process(ob)

        persistent_objects = PersistentInfo.objects.all()

        for persistent_object in persistent_objects:
            print("Persisten object info:{}".format(persistent_object.info))

        self.assertEqual(persistent_objects.count(), 0)
        self.assertEqual(LinkDataController.objects.all().count(), 1)
        self.assertEqual(DomainsController.objects.all().count(), 1)


class ScanLinkJobHandlerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_scan_link(self):
        conf = Configuration.get_object().config_entry
        conf.auto_store_domain_info = True
        conf.save()

        LinkDataController.objects.all().delete()
        DomainsController.objects.all().delete()

        ob = BackgroundJobController.link_scan("https://manually-added-link.com")

        handler = LinkScanJobHandler()
        handler.process(ob)

        persistent_objects = PersistentInfo.objects.all()

        for persistent_object in persistent_objects:
            print("Persisten object info:{}".format(persistent_object.info))

        self.assertEqual(persistent_objects.count(), 0)

        jobs = BackgroundJobController.objects.all()
        for job in jobs:
            print("Job:{} {}".format(job.job, job.subject))

        self.assertEqual(jobs.count(), 1)


class ProcessSourceHandlerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_process_source_unknown(self):
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

        jobs = BackgroundJobController.objects.all()
        for job in jobs:
            print("Job:{} {}".format(job.job, job.subject))

        self.assertEqual(jobs.count(), 1)

    def test_process_source_known(self):
        LinkDataController.objects.all().delete()
        DomainsController.objects.all().delete()
        SourceDataController.objects.all().delete()
        SourceDataController.objects.create(
            url="https://www.youtube.com/feeds/channel=samtime"
        )

        ob = BackgroundJobController.objects.create(
            job=BackgroundJob.JOB_PROCESS_SOURCE,
            subject="https://www.youtube.com/feeds/channel=samtime",
        )

        handler = ProcessSourceJobHandler()
        # call tested function
        result = handler.process(ob)

        persistent_objects = PersistentInfo.objects.all()
        for persistent_object in persistent_objects:
            print("Persisten object info:{}".format(persistent_object.info))

        self.assertEqual(persistent_objects.count(), 0)

        self.assertEqual(result, True)

        jobs = BackgroundJobController.objects.all()
        for job in jobs:
            print("Job:{} {}".format(job.job, job.subject))

        self.assertEqual(jobs.count(), 1)
