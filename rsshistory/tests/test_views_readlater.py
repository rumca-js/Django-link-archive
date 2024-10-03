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
from ..models import ReadLater

from .fakeinternet import FakeInternetTestCase


class ReadLaterViewsTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser", password="testpassword", is_staff=True
        )

    def test_read_later_entries(self):
        entry = LinkDataController.objects.create(
            source_url="https://linkedin.com",
            link="https://linkedin.com/test",
            title="The first link",
            description="the first link description",
            source=None,
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:read-later-entries".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_read_later_add(self):
        entry = LinkDataController.objects.create(
            source_url="https://linkedin.com",
            link="https://linkedin.com/test",
            title="The first link",
            description="the first link description",
            source=None,
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:read-later-add".format(LinkDatabase.name), args=[entry.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_read_later_remove(self):
        entry = LinkDataController.objects.create(
            source_url="https://linkedin.com",
            link="https://linkedin.com/test",
            title="The first link",
            description="the first link description",
            source=None,
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        read_later = ReadLater.objects.create(entry=entry, user=self.user)

        self.client.login(username="testuser", password="testpassword")

        url = reverse(
            "{}:read-later-remove".format(LinkDatabase.name), args=[read_later.id]
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_read_later_clear(self):
        entry = LinkDataController.objects.create(
            source_url="https://linkedin.com",
            link="https://linkedin.com/test",
            title="The first link",
            description="the first link description",
            source=None,
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:read-later-clear".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
