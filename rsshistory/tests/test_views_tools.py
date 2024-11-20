from django.urls import reverse
from django.contrib.auth.models import User

from utils.dateutils import DateUtils

from ..apps import LinkDatabase
from ..controllers import (
    SourceDataController,
    LinkDataController,
    DomainsController,
    BackgroundJobController,
)
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

    def test_show_page_props(self):
        url = reverse("{}:page-show-properties".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_page_show_props_html_get(self):
        MockRequestCounter.mock_page_requests = 0
        url = (
            reverse("{}:get-page-properties".format(LinkDatabase.name))
            + "?page=https://www.linkedin.com"
        )
        response = self.client.get(url)

        # print(response.text.decode('utf-8'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Detected", html=False)

        # two requests: one for page, one for robots.txt
        self.assertEqual(MockRequestCounter.mock_page_requests, 2)

    def test_page_show_props_youtube_get(self):
        MockRequestCounter.mock_page_requests = 0
        url = (
            reverse("{}:get-page-properties".format(LinkDatabase.name))
            + "?page=https://www.youtube.com/watch?v=SwlIAjcYypA"
        )
        response = self.client.get(url)

        # print(response.text.decode('utf-8'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Detected", html=False)
        self.assertEqual(MockRequestCounter.mock_page_requests, 2)

    def test_page_show_props_ytchannel_get(self):
        MockRequestCounter.mock_page_requests = 0
        url = (
            reverse("{}:get-page-properties".format(LinkDatabase.name))
            + "?page=https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"
        )
        response = self.client.get(url)

        # print(response.text.decode('utf-8'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Detected", html=False)

        self.assertEqual(MockRequestCounter.mock_page_requests, 1)

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
