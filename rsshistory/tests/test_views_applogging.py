from datetime import datetime
from pytz import timezone
import logging
from django.urls import reverse
from django.contrib.auth.models import User

from utils.dateutils import DateUtils

from ..apps import LinkDatabase
from ..models import KeyWords, AppLogging

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class AppLoggingViewsTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
            is_staff=True,
        )
        self.client.login(username="testuser", password="testpassword")

    def test_json_logs(self):
        AppLogging.objects.create(
            info_text="text",
            level=int(logging.INFO),
            date=datetime.now(timezone("UTC")),
        )

        url = reverse("{}:json-logs".format(LinkDatabase.name))

        # call tested function
        response = self.client.get(url)

        # redirect to see all jobs
        self.assertEqual(response.status_code, 200)

    def test_json_logs__info(self):
        AppLogging.objects.create(
            info_text="text",
            level=int(logging.INFO),
            date=datetime.now(timezone("UTC")),
        )

        url = reverse("{}:json-logs".format(LinkDatabase.name))
        url = url + "?infos=1"

        # call tested function
        response = self.client.get(url)

        # redirect to see all jobs
        self.assertEqual(response.status_code, 200)
