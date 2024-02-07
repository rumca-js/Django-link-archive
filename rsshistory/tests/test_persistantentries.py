
from ..models import PersistentInfo
from .fakeinternet import FakeInternetTestCase


class BackgroundJobControllerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_persistant_limit(self):

        for item in range(1, 2100):
            PersistentInfo.create("error")

        self.assertEqual(PersistentInfo.objects.all().count(), 1000 + 98)
