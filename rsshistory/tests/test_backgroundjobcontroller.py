from ..controllers import (
    BackgroundJobController,
    LinkDataController,
    SourceDataController,
)
from ..models import BackgroundJob, DataExport
from .fakeinternet import FakeInternetTestCase


class BackgroundJobControllerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()
        self.setup_configuration()

        BackgroundJobController.objects.all().delete()

        ob = SourceDataController.objects.create(
            url="https://youtube.com", title="YouTube", category="No", subcategory="No"
        )
        LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=12345",
            source=ob,
        )

    def tearDown(self):
        BackgroundJobController.objects.all().delete()

    def test_number_of_jobs(self):
        # call tested function
        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(
                BackgroundJob.JOB_LINK_UPDATE_DATA
            ),
            0,
        )

        bj = BackgroundJob.objects.create(
            job=BackgroundJob.JOB_LINK_UPDATE_DATA,
            task=None,
            subject="https://youtube.com?v=1234",
            args="",
            enabled=True,
        )

        # call tested function
        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(
                BackgroundJob.JOB_LINK_UPDATE_DATA
            ),
            1,
        )

        bj = BackgroundJob.objects.create(
            job=BackgroundJob.JOB_PROCESS_SOURCE,
            task=None,
            subject="https://youtube.com?v=1234",
            args="",
            enabled=False,
        )

        # call tested function
        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(
                BackgroundJob.JOB_LINK_UPDATE_DATA
            ),
            1,
        )

    def test_get_job_priority(self):
        # call tested function
        self.assertEqual(
            BackgroundJobController.get_job_priority(BackgroundJob.JOB_PROCESS_SOURCE),
            10,
        )

        # call tested function
        self.assertEqual(
            BackgroundJobController.get_job_priority(BackgroundJob.JOB_LINK_ADD),
            13,
        )

    def test_truncate_invalid_jobs(self):
        invalid_name = "invalid-job-name"

        self.assertEqual(BackgroundJobController.get_number_of_jobs(invalid_name), 0)

        bj = BackgroundJob.objects.create(
            job=invalid_name, task=None, subject="https://youtube.com?v=1234", args=""
        )

        self.assertEqual(BackgroundJobController.get_number_of_jobs(invalid_name), 1)

        # call tested function
        BackgroundJobController.truncate_invalid_jobs()

        self.assertEqual(BackgroundJobController.get_number_of_jobs(invalid_name), 0)

    def test_download_rss(self):
        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(
                BackgroundJob.JOB_PROCESS_SOURCE
            ),
            0,
        )

        source = SourceDataController.objects.all()[0]
        # call tested function
        x = BackgroundJobController.download_rss(source)

        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(
                BackgroundJob.JOB_PROCESS_SOURCE
            ),
            1,
        )

    def test_download_music(self):
        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(
                BackgroundJob.JOB_LINK_DOWNLOAD_MUSIC
            ),
            0,
        )

        link = LinkDataController.objects.all()[0]
        # call tested function
        x = BackgroundJobController.download_music(link)

        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(
                BackgroundJob.JOB_LINK_DOWNLOAD_MUSIC
            ),
            1,
        )

    def test_download_video(self):
        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(
                BackgroundJob.JOB_LINK_DOWNLOAD_VIDEO
            ),
            0,
        )

        link = LinkDataController.objects.all()[0]
        # call tested function
        x = BackgroundJobController.download_video(link)

        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(
                BackgroundJob.JOB_LINK_DOWNLOAD_VIDEO
            ),
            1,
        )

    def test_link_add(self):
        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(BackgroundJob.JOB_LINK_ADD), 0
        )

        source = SourceDataController.objects.all()[0]

        # call tested function
        x = BackgroundJobController.link_add("https://youtube.com?v=1", source)
        # call tested function
        x = BackgroundJobController.link_add("https://youtube.com?v=2", source)
        # call tested function
        x = BackgroundJobController.link_add("https://youtube.com?v=3", source)

        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(BackgroundJob.JOB_LINK_ADD), 3
        )

    def test_write_daily_data_str(self):
        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(
                BackgroundJob.JOB_WRITE_DAILY_DATA
            ),
            0,
        )

        # call tested function
        BackgroundJobController.write_daily_data_str("2022-03-02", "2022-03-04")

        objects = BackgroundJobController.objects.filter(
            job=BackgroundJob.JOB_WRITE_DAILY_DATA
        )

        self.assertEqual(objects.count(), 3)

        self.assertEqual(objects[0].subject, "2022-03-02")
        self.assertEqual(objects[1].subject, "2022-03-03")
        self.assertEqual(objects[2].subject, "2022-03-04")

    def test_write_tag_data(self):
        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(
                BackgroundJob.JOB_WRITE_TOPIC_DATA
            ),
            0,
        )

        # call tested function
        BackgroundJobController.write_tag_data("technofeudalism")

        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(
                BackgroundJob.JOB_WRITE_TOPIC_DATA
            ),
            1,
        )

    def test_import_bookmarks(self):
        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(
                BackgroundJob.JOB_IMPORT_BOOKMARKS
            ),
            0,
        )

        # call tested function
        BackgroundJobController.import_bookmarks()

        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(
                BackgroundJob.JOB_IMPORT_BOOKMARKS
            ),
            1,
        )

    def test_import_sources(self):
        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(
                BackgroundJob.JOB_IMPORT_SOURCES
            ),
            0,
        )

        # call tested function
        BackgroundJobController.import_sources()

        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(
                BackgroundJob.JOB_IMPORT_SOURCES
            ),
            1,
        )

    def test_link_save(self):
        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(BackgroundJob.JOB_LINK_SAVE),
            0,
        )

        # call tested function
        BackgroundJobController.link_save("http://youtube.com?v=676767")

        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(BackgroundJob.JOB_LINK_SAVE),
            1,
        )

    def test_link_download(self):
        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(BackgroundJob.JOB_LINK_DOWNLOAD),
            0,
        )

        # call tested function
        BackgroundJobController.link_download("http://youtube.com?v=676767")

        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(BackgroundJob.JOB_LINK_DOWNLOAD),
            1,
        )

    def test_export_data(self):
        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(BackgroundJob.JOB_EXPORT_DATA),
            0,
        )

        export1 = DataExport.objects.create(
            enabled=True,
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_DAILY_DATA,
            local_path="./daily_dir",
            remote_path="https://github.com/rumca-js/RSS-Link-Database-DAILY.git",
            user="testuser",
            password="password",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=True,
            export_sources=True,
        )

        # call tested function
        BackgroundJobController.export_data(export1)

        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(BackgroundJob.JOB_EXPORT_DATA),
            1,
        )

    def test_on_error(self):
        bj = BackgroundJobController.objects.create(
            job=BackgroundJob.JOB_LINK_UPDATE_DATA,
            task=None,
            subject="https://youtube.com?v=1234",
            args="",
        )

        # call tested function
        bj.on_error()

        self.assertEqual(bj.errors, 1)

        # call tested function
        bj.on_error()

        self.assertEqual(bj.errors, 2)

    def test_enable(self):
        bj = BackgroundJobController.objects.create(
            job=BackgroundJob.JOB_LINK_UPDATE_DATA,
            task=None,
            subject="https://youtube.com?v=1234",
            args="",
            priority=0,
        )

        self.assertTrue(bj.enabled)

        bj.enabled = False
        bj.save()

        # call tested function
        bj.enable()

        self.assertTrue(bj.enabled)
        self.assertEqual(
            bj.priority,
            BackgroundJobController.get_job_priority(
                BackgroundJob.JOB_LINK_UPDATE_DATA
            ),
        )

    def test_update_or_reset_entry(self):
        entry = LinkDataController.objects.all()[0]
        entry.date_update_last = None
        entry.save()

        # call tested functions
        BackgroundJobController.entry_update_data(entry)
        # call tested functions
        BackgroundJobController.entry_reset_data(entry)

        # there can only be update, or reset job

        jobs = BackgroundJobController.objects.all()
        self.assertTrue(jobs.count(), 1)

        job = jobs[0]
        self.assertEqual(job.job, BackgroundJobController.JOB_LINK_UPDATE_DATA)

    def test_reset_or_update_entry(self):
        entry = LinkDataController.objects.all()[0]
        entry.date_update_last = None
        entry.save()

        BackgroundJobController.objects.all().delete()

        # call tested functions
        BackgroundJobController.entry_reset_data(entry)

        jobs = BackgroundJobController.objects.all()
        self.assertTrue(jobs.count(), 1)

        job = jobs[0]
        self.assertEqual(job.job, BackgroundJobController.JOB_LINK_RESET_DATA)

        # call tested functions
        BackgroundJobController.entry_update_data(entry)

        # there can only be update, or reset job

        jobs = BackgroundJobController.objects.all()
        self.assertTrue(jobs.count(), 1)

        job = jobs[0]
        self.assertEqual(job.job, BackgroundJobController.JOB_LINK_RESET_DATA)
