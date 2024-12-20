from django.urls import reverse
from django.contrib.auth.models import User

from utils.dateutils import DateUtils

from ..apps import LinkDatabase
from ..controllers import (
    LinkDataController,
    DomainsController,
    BackgroundJobController,
)

from .fakeinternet import FakeInternetTestCase


class DomainsViewsTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser", password="testpassword", is_staff=True
        )

    def test_domains(self):
        entry = LinkDataController.objects.create(
            source_url="https://linkedin.com",
            link="https://linkedin.com",
            title="The first link",
            description="the first link description",
            language="en",
        )

        DomainsController.objects.create(
                domain = "https://linkedin.com"
        )

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:domains".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_domains_json(self):
        entry = LinkDataController.objects.create(
            source_url="https://linkedin.com",
            link="https://linkedin.com",
            title="The first link",
            description="the first link description",
            language="en",
        )

        DomainsController.objects.create(
                domain = "https://linkedin.com"
        )

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:domains-json".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
