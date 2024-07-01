from pytz import timezone
from datetime import datetime, date
import logging

from ..models import AppLogging
from .fakeinternet import FakeInternetTestCase


class AppLoggingTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_debug(self):
        AppLogging.objects.all().delete()
        # call tested function
        AppLogging.debug("debug")

        self.assertEqual(AppLogging.objects.all().count(), 1)

    def test_info(self):
        AppLogging.objects.all().delete()
        # call tested function
        AppLogging.info("info")

        self.assertEqual(AppLogging.objects.all().count(), 1)

    def test_warning(self):
        AppLogging.objects.all().delete()
        # call tested function
        AppLogging.warning("warning")

        self.assertEqual(AppLogging.objects.all().count(), 1)

    def test_error(self):
        AppLogging.objects.all().delete()

        # call tested function
        AppLogging.error("error")

        self.assertEqual(AppLogging.objects.all().count(), 1)

    def test_exc(self):
        AppLogging.objects.all().delete()

        # call tested function
        AppLogging.exc("exc")

        self.assertEqual(AppLogging.objects.all().count(), 1)

    def test_message_limit(self):
        for item in range(1, 2100):
            # call tested function
            AppLogging.error("error")

        self.assertEqual(AppLogging.objects.all().count(), 1000 + 98)

    def test_cleanup(self):
        AppLogging.objects.create(
            info_text="text",
            level=int(logging.INFO),
            date=datetime.now(timezone("UTC")),
        )

        # call tested function
        AppLogging.cleanup()

    def test_very_long_message(self):
        long_string = "x" * 3001
        AppLogging.objects.create(
            info_text=long_string,
            level=int(logging.INFO),
            date=datetime.now(timezone("UTC")),
        )

        logs = AppLogging.objects.all()
        self.assertTrue(logs.count(), 1)
        self.assertTrue(len(logs[0].info_text), 2000)
