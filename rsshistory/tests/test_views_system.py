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


class SystemViewsTest(FakeInternetTestCase):
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

        # redirect to search
        self.assertEqual(response.status_code, 302)

    def test_admin(self):
        url = reverse("{}:admin-page".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_user_config(self):
        url = reverse("{}:user-config".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_configuration_advanced(self):
        url = reverse("{}:configuration-advanced".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_configuration_json(self):
        url = reverse("{}:configuration-advanced-json".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_system_status(self):
        url = reverse("{}:system-status".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_about(self):
        url = reverse("{}:about".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_reset_config(self):
        url = reverse("{}:reset-config".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_system_status(self):
        url = reverse("{}:system-status".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_wizard(self):
        url = reverse("{}:wizard".format(LinkDatabase.name))

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_wizard_init(self):
        url = reverse("{}:wizard-init".format(LinkDatabase.name))

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_wizard_setup_news(self):
        url = reverse("{}:wizard-setup-news".format(LinkDatabase.name))
        url = url + "?noinitialize=True"

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # we do not initialize block lists
        self.assertEqual(BackgroundJobController.get_number_of_jobs(), 0)

    def test_wizard_setup_gallery(self):
        url = reverse("{}:wizard-setup-gallery".format(LinkDatabase.name))
        url = url + "?noinitialize=True"

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # we do not initialize block lists
        self.assertEqual(BackgroundJobController.get_number_of_jobs(), 0)

    def test_wizard_setup_search_engine(self):
        url = reverse("{}:wizard-setup-search-engine".format(LinkDatabase.name))
        url = url + "?noinitialize=True"

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # we initialize block lists - it will take while
        self.assertEqual(BackgroundJobController.get_number_of_jobs(), 1)

    def test_is_system_ok(self):
        # system should not be ok
        # tasks info is None

        url = reverse("{}:is-system-ok".format(LinkDatabase.name))

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 500)

    def test_json_table_status(self):
        url = reverse("{}:json-table-status".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_json_system_status(self):
        url = reverse("{}:json-system-status".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_json_export_status(self):
        url = reverse("{}:json-export-status".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_get_settings(self):
        url = reverse("{}:get-settings".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_get_indicators(self):
        url = reverse("{}:get-indicators".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        data = response.json()
        print(data)

        self.assertIn("indicators", data)
        self.assertIn("is_reading", data["indicators"])  # source reading indication
        self.assertIn("read_later_queue", data["indicators"])  # used by menu
        self.assertIn("sources_error", data["indicators"])
        self.assertIn("internet_error", data["indicators"])
        self.assertIn("crawling_server_error", data["indicators"])
        self.assertIn("threads_error", data["indicators"])
        self.assertIn("jobs_error", data["indicators"])
        self.assertIn("configuration_error", data["indicators"])
