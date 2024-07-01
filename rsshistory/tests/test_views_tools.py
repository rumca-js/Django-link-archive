from django.urls import reverse
from django.contrib.auth.models import User

from ..apps import LinkDatabase
from ..controllers import (
    SourceDataController,
    LinkDataController,
    DomainsController,
    BackgroundJobController,
)
from ..dateutils import DateUtils
from ..models import KeyWords

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class ToolsViewsTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
            is_staff=True,
        )
        self.client.login(username="testuser", password="testpassword")

    def test_page_show_props(self):
        url = reverse("{}:page-show-props".format(LinkDatabase.name))

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_page_scan_link(self):
        url = reverse("{}:page-scan-link".format(LinkDatabase.name))

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_page_scan_contents(self):
        url = reverse("{}:page-scan-contents".format(LinkDatabase.name))

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_download_url(self):
        url = reverse("{}:download-url".format(LinkDatabase.name))

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_download_music_url(self):
        url = reverse("{}:download-music-url".format(LinkDatabase.name))

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_download_video_url(self):
        url = reverse("{}:download-video-url".format(LinkDatabase.name))

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_is_url_allowed(self):
        url = reverse("{}:is-url-allowed".format(LinkDatabase.name))

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
