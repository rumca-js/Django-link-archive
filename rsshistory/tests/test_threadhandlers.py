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
    SourceAddJobHandler,
    LinkScanJobHandler,
    WriteDailyDataJobHandler,
    ExportDataJobHandler,
    ProcessSourceJobHandler,
)

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class CleanJobHandlerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = self.get_user(
            username="test_username", password="testpassword", is_superuser=True
        )

    def prepare_data(self):
        # inserts old data, we will check if those will be removed
        conf = Configuration.get_object().config_entry
        conf.accept_domain_links = True
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
            domain="youtube.com",
        )
        datetime = KeyWords.get_keywords_date_limit() - timedelta(days=1)
        keyword = KeyWords.objects.create(keyword="test")
        keyword.date_published = datetime
        keyword.save()

    def test_cleanup_job__all(self):
        self.prepare_data()

        job = BackgroundJobController.objects.create(
            job=BackgroundJob.JOB_CLEANUP,
            subject="",
        )

        handler = CleanupJobHandler()
        # call tested function
        handler.process(job)

        jobs = BackgroundJobController.objects.all()
        self.assertEqual(jobs.count(), 18)

    def test_cleanup_job__all_process(self):
        self.prepare_data()

        job = BackgroundJobController.objects.create(
            job=BackgroundJob.JOB_CLEANUP,
            subject="",
        )

        handler = CleanupJobHandler()
        # call tested function
        handler.process(job)

        jobs = BackgroundJobController.objects.all()
        self.assertEqual(jobs.count(), 18)

        for job in jobs:
            handler = CleanupJobHandler()
            # call tested function
            handler.process(job)

        # no exception
        self.assertTrue(True)

    def test_cleanup_job__keywords(self):
        self.prepare_data()

        job = BackgroundJobController.objects.create(
            job=BackgroundJob.JOB_CLEANUP,
            subject="KeyWords",
        )

        handler = CleanupJobHandler()
        handler.process(job)

        # cleanup of links, domains may trigger creating new entries, which may
        # trigger unwanted dependencies

        persistent_objects = AppLogging.objects.filter(level=int(logging.ERROR))

        for persistent_object in persistent_objects:
            print("Persisten object info:{}".format(persistent_object.info_text))

        self.assertEqual(persistent_objects.count(), 0)
        self.assertEqual(KeyWords.objects.all().count(), 0)

        for domain in DomainsController.objects.all():
            print("Domain: {}".format(domain.domain))

    def test_cleanup_job__domains(self):
        self.prepare_data()

        job = BackgroundJobController.objects.create(
            job=BackgroundJob.JOB_CLEANUP,
            subject="DomainsController",
            args=json.dumps({"verify": True}),
        )

        DomainsController.objects.create(
            domain="definitely.domain.to.remove",
        )

        handler = CleanupJobHandler()
        handler.process(job)

        # cleanup of links, domains may trigger creating new entries, which may
        # trigger unwanted dependencies

        persistent_objects = AppLogging.objects.filter(level=int(logging.ERROR))

        for persistent_object in persistent_objects:
            print("Persisten object info:{}".format(persistent_object.info_text))

        self.assertEqual(persistent_objects.count(), 0)

        domains = DomainsController.objects.filter(domain="definitely.domain.to.remove")
        self.assertEqual(domains.count(), 0)

    def test_cleanup_job__disable_domains(self):
        self.prepare_data()

        conf = Configuration.get_object().config_entry
        conf.accept_domain_links = False
        conf.keep_domain_links = False
        conf.enable_domain_support = False
        conf.save()

        job = BackgroundJobController.objects.create(
            job=BackgroundJob.JOB_CLEANUP,
            subject="DomainsController",
        )

        handler = CleanupJobHandler()
        handler.process(job)

        persistent_objects = AppLogging.objects.filter(level=int(logging.ERROR))

        for persistent_object in persistent_objects:
            print("Persisten object info:{}".format(persistent_object.info_text))

        self.assertEqual(persistent_objects.count(), 0)
        self.assertEqual(DomainsController.objects.all().count(), 0)


class LinkAddJobHandlerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = self.get_user(
            username="test_username", password="testpassword", is_superuser=True
        )

    def test_add_link(self):
        conf = Configuration.get_object().config_entry
        conf.accept_domain_links = True
        conf.save()

        LinkDataController.objects.all().delete()
        DomainsController.objects.all().delete()

        ob = BackgroundJobController.link_add("https://manually-added-link.com")
        self.assertTrue(ob)

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
        conf.accept_domain_links = True
        conf.save()

        LinkDataController.objects.all().delete()
        DomainsController.objects.all().delete()

        ob = BackgroundJobController.link_add(
            "https://manually-added-link.com", tag="demoscene"
        )
        self.assertTrue(ob)

        handler = LinkAddJobHandler()
        handler.process(ob)

        persistent_objects = AppLogging.objects.filter(level=int(logging.ERROR))

        self.assertTrue(self.no_errors())

        self.assertEqual(persistent_objects.count(), 0)
        self.assertEqual(LinkDataController.objects.all().count(), 1)
        self.assertEqual(DomainsController.objects.all().count(), 1)


class SourceAddJobHandlerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = self.get_user(
            username="test_username", password="testpassword", is_superuser=True
        )

    def test_add_link(self):
        conf = Configuration.get_object().config_entry
        conf.accept_domain_links = True
        conf.save()

        LinkDataController.objects.all().delete()
        DomainsController.objects.all().delete()

        ob = BackgroundJobController.source_add("https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM")
        self.assertTrue(ob)

        handler = SourceAddJobHandler()
        handler.process(ob)

        persistent_objects = AppLogging.objects.filter(level=int(logging.ERROR))


        self.assertTrue(self.no_errors())

        self.assertEqual(persistent_objects.count(), 0)
        self.assertEqual(LinkDataController.objects.all().count(), 0)
        self.assertEqual(SourceDataController.objects.all().count(), 1)
        self.assertEqual(DomainsController.objects.all().count(), 0)


class ScanLinkJobHandlerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        conf = Configuration.get_object().config_entry
        conf.auto_scan_new_entries = True
        conf.save()

        self.user = self.get_user(
            username="test_username", password="testpassword", is_superuser=True
        )

    def test_scan_link(self):
        conf = Configuration.get_object().config_entry
        conf.accept_domain_links = True
        conf.save()

        LinkDataController.objects.all().delete()
        DomainsController.objects.all().delete()

        ob = BackgroundJobController.link_scan("https://manually-added-link.com")
        self.assertTrue(ob)

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
        MockRequestCounter.mock_page_requests = 0

        LinkDataController.objects.all().delete()
        DomainsController.objects.all().delete()
        SourceDataController.objects.all().delete()
        BackgroundJobController.objects.all().delete()

        source = SourceDataController.objects.create(
            url="https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"
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

        self.assertEqual(MockRequestCounter.mock_page_requests, 1)


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
