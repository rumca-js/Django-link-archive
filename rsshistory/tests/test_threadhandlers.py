from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from ..controllers import (
    BackgroundJobController,
    LinkDataController,
    SourceDataController,
)
from ..models import (
    BackgroundJob,
    PersistentInfo,
    ConfigurationEntry,
    DataExport,
    SourceExportHistory,
)
from ..threadhandlers import HandlerManager, RefreshThreadHandler


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


class RefreshThreadHandlerTest(TestCase):
    def disable_web_pages(self):
        from ..webtools import BasePage, Page

        BasePage.user_agent = None
        Page.user_agent = None
        entry = ConfigurationEntry.get()
        entry.user_agent = ""
        entry.save()

    def setUp(self):
        SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )

        BackgroundJobController.objects.all().delete()
        SourceExportHistory.objects.all().delete()

        self.disable_web_pages()
        entry = ConfigurationEntry.get()

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
                job=BackgroundJobController.JOB_PUSH_TO_REPO
            ).count(),
            1,
        )

        self.assertEqual(
            BackgroundJobController.objects.filter(
                job=BackgroundJobController.JOB_CLEANUP
            ).count(),
            1,
        )
