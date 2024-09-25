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
from ..models import KeyWords, DataExport, UserTags

from .fakeinternet import FakeInternetTestCase


class UserThingsTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser", password="testpassword", is_staff=True
        )

    def test_user_personal(self):
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

        url = reverse("{}:user-personal".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_user_entry_history(self):
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

        url = reverse("{}:user-entry-history".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_user_comments(self):
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

        url = reverse("{}:user-comments".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_user_search_history(self):
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

        url = reverse("{}:user-search-history".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
