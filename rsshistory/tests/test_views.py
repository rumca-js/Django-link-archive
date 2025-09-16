from django.urls import reverse
from django.contrib.auth.models import AnonymousUser, User
from django.test.client import RequestFactory

from utils.dateutils import DateUtils

from ..apps import LinkDatabase
from ..controllers import SourceDataController, LinkDataController, DomainsController
from ..models import KeyWords, DataExport, ConfigurationEntry
from ..configuration import Configuration
from ..views import get_search_term, ViewPage, SimpleViewPage

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


factory = RequestFactory()


class FakeRequest(object):
    def __init__(self, authenticated=False, staff=False):
        request = factory.get('/fake-url/')

        if authenticated:
            username = "testuser"
            if authenticated:
                username="authenticateduser"
            if staff:
                username="staffuser"

            users = User.objects.filter(username=username)
            if users.exists():
                self.user=users[0]
            else:
                self.user = User.objects.create_user(username=username, password='testpass', is_staff=staff)
        else:
            self.user = AnonymousUser()

        self.GET = {}



class GenericViewsTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_get_search_term(self):
        themap = {"search": "something1 = else & something2 = else2"}

        # call tested function
        term = get_search_term(themap)

        self.assertEqual(term, "something1 = else & something2 = else2")


class SimpleViewPageTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.staff = User.objects.create_user(
            username="staff",
            password="testpassword",
            is_staff=True,
        )
        self.nonstaff = User.objects.create_user(
            username="nonstaff",
            password="testpassword",
            is_staff=False,
        )

    def test_is_allowed__none(self):
        page = SimpleViewPage(None)
        self.assertFalse(page.is_allowed())

    def test_is_allowed__all_authenticated(self):
        request = FakeRequest(authenticated=True, staff=False)
        page = SimpleViewPage(request=request, view_access_type=ConfigurationEntry.ACCESS_TYPE_ALL)
        self.assertTrue(page.is_allowed())

    def test_is_allowed__all_authenticated__staff(self):
        request = FakeRequest(authenticated=True, staff=True)
        page = SimpleViewPage(request=request, view_access_type=ConfigurationEntry.ACCESS_TYPE_ALL)
        self.assertTrue(page.is_allowed())

    def test_is_allowed__logged__authenticated(self):
        request = FakeRequest(authenticated=True, staff=False)
        page = SimpleViewPage(request=request, view_access_type=ConfigurationEntry.ACCESS_TYPE_LOGGED)
        self.assertTrue(page.is_allowed())

    def test_is_allowed__logged__authenticated__staff(self):
        request = FakeRequest(authenticated=True, staff=True)
        page = SimpleViewPage(request=request, view_access_type=ConfigurationEntry.ACCESS_TYPE_LOGGED)
        self.assertTrue(page.is_allowed())

    def test_is_allowed__staff_authenticated(self):
        request = FakeRequest(authenticated=True, staff=False)
        page = SimpleViewPage(request=request, view_access_type=ConfigurationEntry.ACCESS_TYPE_STAFF)
        self.assertFalse(page.is_allowed())

    def test_is_allowed__staff_authenticated__staff(self):
        request = FakeRequest(authenticated=True, staff=True)
        page = SimpleViewPage(request=request, view_access_type=ConfigurationEntry.ACCESS_TYPE_STAFF)
        self.assertTrue(page.is_allowed())

    def test_access_rights__nouser__all(self):
        config_entry = Configuration.get_object().config_entry
        config_entry.view_access_type = ConfigurationEntry.ACCESS_TYPE_ALL
        Configuration.get_object().config_entry = config_entry

        # self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:entries".format(LinkDatabase.name))
        response = self.client.get(url)
        page_source = response.content.decode("utf-8")

        access_text = "User does not have rights"

        self.assertFalse(page_source.find(access_text) >= 0)

    def test_access_rights__nouser__auth(self):
        config_entry = Configuration.get_object().config_entry
        config_entry.view_access_type = ConfigurationEntry.ACCESS_TYPE_LOGGED
        Configuration.get_object().config_entry = config_entry

        # self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:entries".format(LinkDatabase.name))
        response = self.client.get(url)
        page_source = response.content.decode("utf-8")
        # print(page_source)

        access_text = "User does not have rights"

        self.assertTrue(page_source.find(access_text) >= 0)

    def test_access_rights__nouser__staff(self):
        config_entry = Configuration.get_object().config_entry
        config_entry.view_access_type = ConfigurationEntry.ACCESS_TYPE_STAFF
        Configuration.get_object().config_entry = config_entry

        # self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:entries".format(LinkDatabase.name))
        response = self.client.get(url)
        page_source = response.content.decode("utf-8")
        # print(page_source)

        access_text = "User does not have rights"

        self.assertTrue(page_source.find(access_text) >= 0)

    def test_access_rights__nouser__owner(self):
        config_entry = Configuration.get_object().config_entry
        config_entry.view_access_type = ConfigurationEntry.ACCESS_TYPE_OWNER
        Configuration.get_object().config_entry = config_entry

        # self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:entries".format(LinkDatabase.name))
        response = self.client.get(url)
        page_source = response.content.decode("utf-8")
        # print(page_source)

        access_text = "User does not have rights"

        self.assertTrue(page_source.find(access_text) >= 0)

    def test_access_rights__authenticated__all(self):
        config_entry = Configuration.get_object().config_entry
        config_entry.view_access_type = ConfigurationEntry.ACCESS_TYPE_ALL
        Configuration.get_object().config_entry = config_entry

        self.client.login(username="nonstaff", password="testpassword")

        url = reverse("{}:entries".format(LinkDatabase.name))
        response = self.client.get(url)
        page_source = response.content.decode("utf-8")

        access_text = "User does not have rights"

        self.assertFalse(page_source.find(access_text) >= 0)

    def test_access_rights__authenticated__logged(self):
        config_entry = Configuration.get_object().config_entry
        config_entry.view_access_type = ConfigurationEntry.ACCESS_TYPE_LOGGED
        Configuration.get_object().config_entry = config_entry

        self.client.login(username="nonstaff", password="testpassword")

        url = reverse("{}:entries".format(LinkDatabase.name))
        response = self.client.get(url)
        page_source = response.content.decode("utf-8")

        access_text = "User does not have rights"

        self.assertFalse(page_source.find(access_text) >= 0)

    def test_access_rights__authenticated__staff(self):
        config_entry = Configuration.get_object().config_entry
        config_entry.view_access_type = ConfigurationEntry.ACCESS_TYPE_STAFF
        config_entry.save()
        Configuration.get_object().config_entry = config_entry

        self.client.login(username="nonstaff", password="testpassword")

        url = reverse("{}:entries".format(LinkDatabase.name))
        response = self.client.get(url)
        page_source = response.content.decode("utf-8")

        # print(page_source)

        access_text = "User does not have rights"

        self.assertTrue(page_source.find(access_text) >= 0)

    def test_access_rights__authenticated__owner(self):
        config_entry = Configuration.get_object().config_entry
        config_entry.view_access_type = ConfigurationEntry.ACCESS_TYPE_OWNER
        Configuration.get_object().config_entry = config_entry

        self.client.login(username="nonstaff", password="testpassword")

        url = reverse("{}:entries".format(LinkDatabase.name))
        response = self.client.get(url)
        page_source = response.content.decode("utf-8")

        access_text = "User does not have rights"

        self.assertTrue(page_source.find(access_text) >= 0)

    def test_access_rights__staff__all(self):
        config_entry = Configuration.get_object().config_entry
        config_entry.view_access_type = ConfigurationEntry.ACCESS_TYPE_ALL
        Configuration.get_object().config_entry = config_entry

        self.client.login(username="staff", password="testpassword", is_staff=True)

        url = reverse("{}:entries".format(LinkDatabase.name))
        response = self.client.get(url)
        page_source = response.content.decode("utf-8")

        access_text = "User does not have rights"

        self.assertFalse(page_source.find(access_text) >= 0)

    def test_access_rights__staff__logged(self):
        config_entry = Configuration.get_object().config_entry
        config_entry.view_access_type = ConfigurationEntry.ACCESS_TYPE_LOGGED
        Configuration.get_object().config_entry = config_entry

        self.client.login(username="staff", password="testpassword", is_staff=True)

        url = reverse("{}:entries".format(LinkDatabase.name))
        response = self.client.get(url)
        page_source = response.content.decode("utf-8")

        access_text = "User does not have rights"

        self.assertFalse(page_source.find(access_text) >= 0)

    def test_access_rights__staff__staff(self):
        config_entry = Configuration.get_object().config_entry
        config_entry.view_access_type = ConfigurationEntry.ACCESS_TYPE_STAFF
        Configuration.get_object().config_entry = config_entry

        self.client.login(username="staff", password="testpassword", is_staff=True)

        url = reverse("{}:entries".format(LinkDatabase.name))
        response = self.client.get(url)
        page_source = response.content.decode("utf-8")

        access_text = "User does not have rights"

        self.assertFalse(page_source.find(access_text) >= 0)

    def test_access_rights__staff__owner(self):
        config_entry = Configuration.get_object().config_entry
        config_entry.view_access_type = ConfigurationEntry.ACCESS_TYPE_OWNER
        Configuration.get_object().config_entry = config_entry

        self.client.login(username="staff", password="testpassword", is_staff=True)

        url = reverse("{}:entries".format(LinkDatabase.name))
        response = self.client.get(url)
        page_source = response.content.decode("utf-8")

        access_text = "User does not have rights"

        self.assertTrue(page_source.find(access_text) >= 0)


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
        context = page.init_context(context)

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
