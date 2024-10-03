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

    def test_wizard_setup_news(self):
        url = reverse("{}:wizard-setup-news".format(LinkDatabase.name))
        url = url + "?noinitialize=True"

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(BackgroundJobController.get_number_of_jobs(), 1)

    def test_wizard_setup_gallery(self):
        url = reverse("{}:wizard-setup-gallery".format(LinkDatabase.name))
        url = url + "?noinitialize=True"

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(BackgroundJobController.get_number_of_jobs(), 1)

    def test_wizard_setup_search_engine(self):
        url = reverse("{}:wizard-setup-search-engine".format(LinkDatabase.name))
        url = url + "?noinitialize=True"

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(BackgroundJobController.get_number_of_jobs(), 1)

    def test_is_system_ok(self):
        # system should not be ok
        # tasks info is None

        url = reverse("{}:is-system-ok".format(LinkDatabase.name))

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 500)
