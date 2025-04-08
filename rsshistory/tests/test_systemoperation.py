from datetime import datetime, timedelta

from ..models import SystemOperation, BackgroundJob, BackgroundJobHistory
from ..controllers import SystemOperationController
from ..configuration import Configuration

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class SystemOperationTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_refresh__refreshprocessor(self):
        SystemOperation.objects.all().delete()

        # call tested function
        SystemOperationController().refresh("RefreshProcessor")

        operations = SystemOperation.objects.all()
        self.assertEqual(operations.count(), 2)
        self.assertEqual(operations[0].check_type, "CrawlingServer")
        self.assertEqual(operations[0].status, True)
        self.assertEqual(operations[1].check_type, "Internet")
        self.assertEqual(operations[1].status, True)

    def test_refresh__not_refreshprocessor(self):
        SystemOperation.objects.all().delete()

        # call tested function
        SystemOperationController().refresh("NotRefreshProcessor")
        SystemOperationController().refresh("NotRefreshProcessor")

        operations = SystemOperation.objects.all()
        self.assertEqual(operations.count(), 3)

        self.assertEqual(operations[0].check_type, "")
        self.assertEqual(operations[0].status, True)

        self.assertEqual(operations[1].check_type, "CrawlingServer")
        self.assertEqual(operations[1].status, True)

        self.assertEqual(operations[2].check_type, "Internet")
        self.assertEqual(operations[2].status, True)

    def test_refresh__adds_multiple(self):
        SystemOperation.objects.all().delete()

        # only last one is important

        # call tested function
        SystemOperationController().refresh("RefreshProcessor")
        SystemOperationController().refresh("RefreshProcessor")

        operations = SystemOperation.objects.all()
        self.assertEqual(operations.count(), 3)

        self.assertEqual(operations[0].check_type, "")
        self.assertEqual(operations[0].status, True)

        self.assertEqual(operations[1].check_type, "CrawlingServer")
        self.assertEqual(operations[1].status, True)

        self.assertEqual(operations[2].check_type, "Internet")
        self.assertEqual(operations[2].status, True)

    def test_is_threading_ok(self):
        SystemOperation.objects.all().delete()

        controller = SystemOperationController()
        controller.refresh("RefreshProcessor")

        # call tested function
        self.assertTrue(controller.is_threading_ok())

    def test_is_threading_ok(self):
        SystemOperation.objects.all().delete()

        controller = SystemOperationController()
        controller.refresh("RefreshProcessor")

        # call tested function
        self.assertTrue(controller.last_operation_status())

    def test_get_threads(self):
        SystemOperation.objects.all().delete()

        controller = SystemOperationController()
        controller.refresh("RefreshProcessor")
        controller.refresh("NotRefreshProcessor")

        # call tested function
        threads = SystemOperationController.get_threads()
        self.assertEqual(len(threads), 2)
        self.assertIn("RefreshProcessor", threads)
        self.assertIn("NotRefreshProcessor", threads)

    def test_get_thread_info(self):
        SystemOperation.objects.all().delete()

        controller = SystemOperationController()
        controller.refresh("RefreshProcessor")
        controller.refresh("NotRefreshProcessor")

        # call tested function
        thread_info = controller.get_thread_info("RefreshProcessor")

        self.assertTrue(thread_info)
        self.assertEqual(len(thread_info), 3)
        self.assertEqual(thread_info[0], "RefreshProcessor")

    def test_cleanup__removes(self):
        SystemOperation.objects.all().delete()

        controller = SystemOperationController()
        controller.refresh("RefreshProcessor")
        controller.refresh("NotRefreshProcessor")

        thread_ids = [
            "RefreshProcessor",
            "XRefreshProcessor",
        ]

        # call tested function
        SystemOperationController.cleanup(cfg={}, thread_ids=thread_ids)

        rows = SystemOperation.objects.all()

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].thread_id, "RefreshProcessor")

    def test_is_time_to_cleanup__yes(self):
        SystemOperation.objects.all().delete()

        BackgroundJobHistory.objects.all().delete()

        controller = SystemOperationController()

        # call tested function
        is_time = controller.is_time_to_cleanup()

        self.assertTrue(is_time)

    def test_is_time_to_cleanup__no(self):
        SystemOperation.objects.all().delete()
        BackgroundJobHistory.objects.all().delete()

        BackgroundJobHistory.objects.create(job=BackgroundJob.JOB_CLEANUP, subject="")

        controller = SystemOperationController()

        # call tested function
        is_time = controller.is_time_to_cleanup()

        self.assertFalse(is_time)

    def test_is_time_to_cleanup__yes__realy_old(self):
        SystemOperation.objects.all().delete()

        date = datetime.now() - timedelta(days=1)

        job = BackgroundJobHistory.objects.create(
            job=BackgroundJob.JOB_CLEANUP, subject="", date_created=date
        )
        job.date_created = date
        job.save()

        controller = SystemOperationController()

        # call tested function
        is_time = controller.is_time_to_cleanup()

        self.assertTrue(is_time)
