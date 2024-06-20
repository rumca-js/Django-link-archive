from django.urls import reverse
from django.contrib.auth.models import User

from ..apps import LinkDatabase
from ..models import ModelFiles
from ..configuration import Configuration

from .fakeinternet import FakeInternetTestCase


class ModelFilesTests(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()
        c = Configuration.get_object().config_entry
        c.enable_file_support = True
        c.save()

        self.user = User.objects.create_user(
            username="testuser", password="testpassword", is_staff=True
        )

    def test_model_files(self):
        ModelFiles.objects.all().delete()
        data = "data"
        obj = ModelFiles.objects.create(file_name = "test", contents = data.encode())

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:model-files".format(LinkDatabase.name))

        # call user action
        response = self.client.get(url)

        # redirect to view the link again
        self.assertEqual(response.status_code, 200)

    def test_model_file(self):
        ModelFiles.objects.all().delete()
        data = "data"
        obj = ModelFiles.objects.create(file_name = "test", contents = data.encode())

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:model-file".format(LinkDatabase.name), args=[obj.id])

        # call user action
        response = self.client.get(url)

        # redirect to view the link again
        self.assertEqual(response.status_code, 200)
