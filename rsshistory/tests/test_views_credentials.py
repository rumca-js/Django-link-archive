from django.urls import reverse
from django.contrib.auth.models import User

from utils.dateutils import DateUtils

from ..apps import LinkDatabase
from ..models import Credentials

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class CredentialsViewsTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
            is_staff=True,
        )
        self.client.login(username="testuser", password="testpassword")

    def test_credential_add(self):
        url = reverse("{}:credential-add".format(LinkDatabase.name))

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_credential_edit(self):
        key = Credentials.objects.create(name="test")

        url = reverse("{}:credential-edit".format(LinkDatabase.name), args=[key.id])

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_credential_remove(self):
        key = Credentials.objects.create(name="test")

        url = reverse("{}:credential-remove".format(LinkDatabase.name), args=[key.id])

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)

        objects = Credentials.objects.all()
        self.assertFalse(objects.exists())

    def test_credentials(self):
        key = Credentials.objects.create(name="test")

        url = reverse("{}:credentials".format(LinkDatabase.name))

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

