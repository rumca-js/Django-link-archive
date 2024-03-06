from ..models import AppLogging
from .fakeinternet import FakeInternetTestCase


class AppLoggingTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_persistant_limit(self):
        for item in range(1, 2100):
            AppLogging.error("error")

        self.assertEqual(AppLogging.objects.all().count(), 1000 + 98)
