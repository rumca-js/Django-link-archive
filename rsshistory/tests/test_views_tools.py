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
from ..configuration import Configuration

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
        url = reverse("{}:page-show-props".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_get_page_properties__html_get(self):
        MockRequestCounter.mock_page_requests = 0
        url = (
            reverse("{}:get-page-properties".format(LinkDatabase.name))
            + "?link=https://www.linkedin.com"
        )
        response = self.client.get(url)

        # print(response.text.decode('utf-8'))

        self.assertEqual(response.status_code, 200)

        # two requests: one for page, one for robots.txt
        self.assertEqual(MockRequestCounter.mock_page_requests, 1)

    def test_get_page_properties__youtube_get(self):
        MockRequestCounter.mock_page_requests = 0
        url = (
            reverse("{}:get-page-properties".format(LinkDatabase.name))
            + "?link=https://www.youtube.com/watch?v=SwlIAjcYypA"
        )
        response = self.client.get(url)

        # print(response.text.decode('utf-8'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(MockRequestCounter.mock_page_requests, 1)

    def test_get_page_properties__ytchannel_get(self):
        MockRequestCounter.mock_page_requests = 0
        url = (
            reverse("{}:get-page-properties".format(LinkDatabase.name))
            + "?link=https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"
        )
        response = self.client.get(url)

        # print(response.text.decode('utf-8'))

        self.assertEqual(response.status_code, 200)

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

    def test_cleanup_link(self):
        MockRequestCounter.mock_page_requests = 0
        url = (
            reverse("{}:cleanup-link".format(LinkDatabase.name))
            + "?link=https://www.linkedin.com"
        )
        response = self.client.get(url)

        # print(response.text.decode('utf-8'))

        self.assertEqual(response.status_code, 200)

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_cleanup_link_json(self):
        MockRequestCounter.mock_page_requests = 0
        url = (
            reverse("{}:cleanup-link-json".format(LinkDatabase.name))
            + "?link=https://www.linkedin.com"
        )
        response = self.client.get(url)

        # print(response.text.decode('utf-8'))

        self.assertEqual(response.status_code, 200)

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_link_input_suggestions_json__no_slash(self):
        MockRequestCounter.mock_page_requests = 0
        url = (
            reverse("{}:link-input-suggestions-json".format(LinkDatabase.name))
            + "?link=https://www.linkedin.com/"
        )
        response = self.client.get(url)

        # print(response.text.decode('utf-8'))

        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertIn("https://www.linkedin.com", data["links"])

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_link_input_suggestions_json__https(self):
        config = Configuration.get_object().config_entry
        config.prefer_https_links = True
        config.save()

        MockRequestCounter.mock_page_requests = 0
        url = (
            reverse("{}:link-input-suggestions-json".format(LinkDatabase.name))
            + "?link=http://www.linkedin.com/"
        )
        response = self.client.get(url)

        # print(response.text.decode('utf-8'))

        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertIn("https://www.linkedin.com/", data["links"])

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_link_input_suggestions_json__no_www(self):
        config = Configuration.get_object().config_entry
        config.prefer_non_www_links = True
        config.save()

        MockRequestCounter.mock_page_requests = 0
        url = (
            reverse("{}:link-input-suggestions-json".format(LinkDatabase.name))
            + "?link=https://www.linkedin.com/"
        )
        response = self.client.get(url)

        # print(response.text.decode('utf-8'))

        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertIn("https://linkedin.com/", data["links"])

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_link_input_suggestions_json__domain(self):
        config = Configuration.get_object().config_entry
        config.accept_non_domain_links = False
        config.save()

        MockRequestCounter.mock_page_requests = 0
        url = (
            reverse("{}:link-input-suggestions-json".format(LinkDatabase.name))
            + "?link=https://www.linkedin.com/something"
        )
        response = self.client.get(url)

        # print(response.text.decode('utf-8'))

        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertIn("https://www.linkedin.com", data["links"])

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)
