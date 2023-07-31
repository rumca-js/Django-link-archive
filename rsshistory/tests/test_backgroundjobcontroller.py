from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from ..controllers import (
    BackgroundJobController,
    LinkDataController,
    SourceDataController,
)
from ..models import BackgroundJob, PersistentInfo


class BackgroundJobControllerTest(TestCase):
    def setUp(self):
        ob = SourceDataController.objects.create(
            url="https://youtube.com", title="YouTube", category="No", subcategory="No"
        )
        LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=12345",
            source_obj=ob,
        )

        # pers = PersistentInfo.objects.all()
        # self.assertEqual(pers[0].info, "")
        # self.assertEqual(len(pers), 0)

    def test_number_of_jobs(self):
        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(BackgroundJob.JOB_LINK_DETAILS),
            0,
        )

        bj = BackgroundJob.objects.create(
            job=BackgroundJob.JOB_LINK_DETAILS,
            task=None,
            subject="https://youtube.com?v=1234",
            args="",
        )

        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(BackgroundJob.JOB_LINK_DETAILS),
            1,
        )

    def test_truncate_invalid_jobs(self):
        invalid_name = "invalid-job-name"

        self.assertEqual(BackgroundJobController.get_number_of_jobs(invalid_name), 0)

        bj = BackgroundJob.objects.create(
            job=invalid_name, task=None, subject="https://youtube.com?v=1234", args=""
        )

        self.assertEqual(BackgroundJobController.get_number_of_jobs(invalid_name), 1)

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
        x = BackgroundJobController.download_video(link)

        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(
                BackgroundJob.JOB_LINK_DOWNLOAD_VIDEO
            ),
            1,
        )

    def test_youtube_details(self):
        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(BackgroundJob.JOB_LINK_DETAILS),
            0,
        )

        x = BackgroundJobController.youtube_details("https://youtube.com?v=1234")

        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(BackgroundJob.JOB_LINK_DETAILS),
            1,
        )

    def test_link_add(self):
        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(BackgroundJob.JOB_LINK_ADD), 0
        )

        source = SourceDataController.objects.all()[0]

        x = BackgroundJobController.link_add("https://youtube.com?v=1", source)
        x = BackgroundJobController.link_add("https://youtube.com?v=2", source)
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

        BackgroundJobController.write_daily_data_str("2022-03-02", "2022-03-04")

        objects = BackgroundJobController.objects.filter(
            job=BackgroundJob.JOB_WRITE_DAILY_DATA
        )

        self.assertEqual(len(objects), 3)

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

        BackgroundJobController.write_tag_data("technofeudalism")

        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(
                BackgroundJob.JOB_WRITE_TOPIC_DATA
            ),
            1,
        )

    def test_write_bookmarks(self):
        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(
                BackgroundJob.JOB_WRITE_BOOKMARKS
            ),
            0,
        )

        BackgroundJobController.write_bookmarks()

        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(
                BackgroundJob.JOB_WRITE_BOOKMARKS
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

        BackgroundJobController.import_sources()

        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(
                BackgroundJob.JOB_IMPORT_SOURCES
            ),
            1,
        )

    def test_link_archive(self):
        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(BackgroundJob.JOB_LINK_ARCHIVE),
            0,
        )

        BackgroundJobController.link_archive("http://youtube.com?v=676767")

        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(BackgroundJob.JOB_LINK_ARCHIVE),
            1,
        )

    def test_link_download(self):
        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(BackgroundJob.JOB_LINK_DOWNLOAD),
            0,
        )

        BackgroundJobController.link_download("http://youtube.com?v=676767")

        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(BackgroundJob.JOB_LINK_DOWNLOAD),
            1,
        )

    def test_push_to_repo(self):
        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(BackgroundJob.JOB_PUSH_TO_REPO),
            0,
        )

        BackgroundJobController.push_to_repo("2022-03-01")

        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(BackgroundJob.JOB_PUSH_TO_REPO),
            1,
        )

    def test_push_daily_data_to_repo(self):
        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(
                BackgroundJob.JOB_PUSH_DAILY_DATA_TO_REPO
            ),
            0,
        )

        BackgroundJobController.push_daily_data_to_repo("2022-03-01")

        self.assertEqual(
            BackgroundJobController.get_number_of_jobs(
                BackgroundJob.JOB_PUSH_DAILY_DATA_TO_REPO
            ),
            1,
        )
