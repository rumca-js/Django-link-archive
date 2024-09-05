from ..models import SystemOperation
from ..tasks import get_processors, get_tasks

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class SystemOperationTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_get_thread_ids(self):
        thread_ids = SystemOperation.get_thread_ids()

        self.assertEqual(len(thread_ids), len(get_tasks()))
