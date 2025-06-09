from django.urls import reverse
from django.contrib.auth.models import User

from utils.dateutils import DateUtils

from ..apps import LinkDatabase
from ..models import ApiKeys

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class ApiKeysViewsTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
            is_staff=True,
        )
        self.client.login(username="testuser", password="testpassword")

    def test_api_key_add(self):
        url = reverse("{}:api-key-add".format(LinkDatabase.name))

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_api_key_edit(self):
        key = ApiKeys.objects.create(key="test")

        url = reverse("{}:api-key-edit".format(LinkDatabase.name), pk=key.id)

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_api_key_remove(self):
        key = ApiKeys.objects.create(key="test")

        url = reverse("{}:api-key-remove".format(LinkDatabase.name), pk=key.id)

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        objects = ApiKeys.objects.all()
        self.assertFalse(objects.exists())

    def test_api_keys(self):
        key = ApiKeys.objects.create(key="test")

        url = reverse("{}:api-keys".format(LinkDatabase.name))

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

