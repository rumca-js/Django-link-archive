from django.urls import reverse
from django.contrib.auth.models import User

from utils.dateutils import DateUtils

from ..apps import LinkDatabase
from ..controllers import SourceDataController, LinkDataController, DomainsController
from ..models import KeyWords, DataExport

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class ViewsTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
            is_staff=True,
        )
        self.client.login(username="testuser", password="testpassword")

    def test_index(self):
        url = reverse("{}:index".format(LinkDatabase.name))
        response = self.client.get(url)

        # redirect to search init
        self.assertEqual(response.status_code, 302)

    """
    Sources
    """

    def test_sources(self):
        url = reverse("{}:sources".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_source_remove_all(self):
        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:sources-remove-all".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_sources_refresh_all(self):
        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:sources-manual-refresh".format(LinkDatabase.name))
        response = self.client.get(url)

        # redirect
        self.assertEqual(response.status_code, 302)

    """ TODO
    def test_entry_download_music(self):
        url = reverse("{}:entry-download-music".format(LinkDatabase.name), args=[0])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_entry_download_video(self):
        url = reverse("{}:entry-download-video".format(LinkDatabase.name), args=[0])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_entry_download(self):
        url = reverse("{}:entry-download".format(LinkDatabase.name), args=[0])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_entry_save(self):
        url = reverse("{}:entry-save".format(LinkDatabase.name), args=[0])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
    """

    """
    Other views
    """

    def test_show_page_props(self):
        url = reverse("{}:page-show-props".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_page_show_props_html_get(self):
        MockRequestCounter.mock_page_requests = 0
        url = (
            reverse("{}:page-show-props".format(LinkDatabase.name))
            + "?page=https://www.linkedin.com"
        )
        response = self.client.get(url)

        # print(response.text.decode('utf-8'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Detected", html=False)

        # two requests: one for page, one for robots.txt
        self.assertEqual(MockRequestCounter.mock_page_requests, 2)

    def test_page_show_props_html_post(self):
        MockRequestCounter.mock_page_requests = 0
        url = reverse("{}:page-show-props".format(LinkDatabase.name))

        data = {"link": "https://www.linkedin.com"}
        response = self.client.post(url, data=data)

        # print(response.text.decode('utf-8'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Detected", html=False)

        # two requests: one for page, one for robots.txt
        self.assertEqual(MockRequestCounter.mock_page_requests, 1)

    def test_page_show_props_youtube_get(self):
        MockRequestCounter.mock_page_requests = 0
        url = (
            reverse("{}:page-show-props".format(LinkDatabase.name))
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
            reverse("{}:page-show-props".format(LinkDatabase.name))
            + "?page=https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"
        )
        response = self.client.get(url)

        # print(response.text.decode('utf-8'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Detected", html=False)

        # one to read RSS, one to read HTML page for thumbnail
        self.assertEqual(MockRequestCounter.mock_page_requests, 2)

    def test_page_scan_contents(self):
        url = reverse("{}:page-scan-contents".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_page_scan_link(self):
        url = reverse("{}:page-scan-link".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_page_scan_input_html(self):
        MockRequestCounter.mock_page_requests = 0

        url = (
            reverse("{}:page-scan-link".format(LinkDatabase.name))
            + "?link=https://www.linkedin.com"
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(MockRequestCounter.mock_page_requests, 1)

    def test_import_bookmarks(self):
        url = reverse("{}:import-bookmarks".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_import_daily_data(self):
        url = reverse("{}:import-daily-data".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_import_sources(self):
        url = reverse("{}:import-sources".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_push_daily_data_form(self):
        url = reverse("{}:push-daily-data-form".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_domains(self):
        url = reverse("{}:domains".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
