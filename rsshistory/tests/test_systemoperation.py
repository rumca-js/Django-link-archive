from ..models import SystemOperation
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
        self.assertEqual(operations.count(), 1)
        self.assertEqual(operations[0].is_internet_connection_checked, True)
        self.assertEqual(operations[0].is_internet_connection_ok, True)

    def test_refresh__not_refreshprocessor(self):
        SystemOperation.objects.all().delete()

        # call tested function
        SystemOperationController().refresh("NotRefreshProcessor")

        operations = SystemOperation.objects.all()
        self.assertEqual(operations.count(), 1)
        self.assertEqual(operations[0].is_internet_connection_checked, False)

    def test_refresh__adds_multiple(self):
        SystemOperation.objects.all().delete()

        # only last one is important

        # call tested function
        SystemOperationController().refresh("RefreshProcessor")
        SystemOperationController().refresh("RefreshProcessor")

        operations = SystemOperation.objects.all()
        self.assertEqual(operations.count(), 1)
        self.assertEqual(operations[0].is_internet_connection_checked, True)
        self.assertEqual(operations[0].is_internet_connection_ok, True)

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
        self.assertTrue(controller.get_last_internet_status())

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
        self.assertEqual(len(thread_info), 2)
        self.assertEqual(thread_info[0], "RefreshProcessor")

    def test_cleanup__removes(self):
        SystemOperation.objects.all().delete()

        controller = SystemOperationController()
        controller.refresh("RefreshProcessor")
        controller.refresh("NotRefreshProcessor")

        thread_ids = [
                'RefreshProcessor',
                'XRefreshProcessor',
        ]

        # call tested function
        SystemOperationController.cleanup(cfg={}, thread_ids=thread_ids)

        rows = SystemOperation.objects.all()

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].thread_id, "RefreshProcessor")
