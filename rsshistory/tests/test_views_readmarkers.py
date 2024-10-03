from django.urls import reverse
from django.contrib.auth.models import User

from ..apps import LinkDatabase
from ..models import ReadMarkers
from ..configuration import Configuration
from ..controllers import SourceDataController

from .fakeinternet import FakeInternetTestCase


class ReadMarkerTests(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()
        c = Configuration.get_object().config_entry
        c.enable_file_support = True
        c.save()

        self.user = User.objects.create_user(
            username="testuser", password="testpassword", is_staff=True
        )

    def test_set_read_marker(self):
        ReadMarkers.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:set-read-marker".format(LinkDatabase.name))

        # call user action
        response = self.client.get(url)

        # redirect to view the link again
        self.assertEqual(response.status_code, 302)

    def test_set_source_read_marker(self):
        source = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            export_to_cms=True,
        )

        ReadMarkers.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        url = reverse(
            "{}:set-source-read-marker".format(LinkDatabase.name), args=[source.id]
        )

        # call user action
        response = self.client.get(url)

        # redirect to view the link again
        self.assertEqual(response.status_code, 302)
