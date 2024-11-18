from ..models import SystemOperation
from ..controllers import SystemOperationController
from ..configuration import Configuration
from ..tasks import get_tasks

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class SystemOperationTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_get_task_ids(self):
        # call tested function
        task_ids = SystemOperationController().get_thread_ids()

        self.assertEqual(len(task_ids), len(get_tasks()))

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
