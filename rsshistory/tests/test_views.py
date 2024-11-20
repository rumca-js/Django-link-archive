from django.urls import reverse
from django.contrib.auth.models import User

from utils.dateutils import DateUtils

from ..apps import LinkDatabase
from ..controllers import SourceDataController, LinkDataController, DomainsController
from ..models import KeyWords, DataExport
from ..views import get_search_term, ViewPage

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class GenericViewsTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_get_search_term(self):
        themap = {"search": "something1 = else & something2 = else2"}

        # call tested function
        term = get_search_term(themap)

        self.assertEqual(term, "something1 = else & something2 = else2")


class ViewPageTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
            is_staff=True,
        )

    def test_init_context(self):
        page = ViewPage(None)

        context = {}

        # call tested function
        term = page.init_context(context)

        self.assertFalse(context["is_user_allowed"])
        self.assertTrue(context["view"])
        self.assertTrue(context["user_config"])
        self.assertTrue(context["config"])


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

    """
    Other views
    """

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
