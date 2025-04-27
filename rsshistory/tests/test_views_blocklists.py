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
from ..models import BlockEntryList, BlockEntry

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class BlockListViewsTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
            is_staff=True,
        )
        self.client.login(username="testuser", password="testpassword")

    def test_block_list_initialize(self):
        url = reverse("{}:block-lists-initialize".format(LinkDatabase.name))

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        lists = BlockEntryList.objects.all()
        self.assertTrue(lists.exists())

    def test_block_lists(self):
        url = reverse("{}:block-lists".format(LinkDatabase.name))

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_block_lists_json(self):
        url = reverse("{}:block-lists-json".format(LinkDatabase.name))

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_block_lists_update(self):
        url = reverse("{}:block-lists-update".format(LinkDatabase.name))

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_block_lists_clear(self):
        url = reverse("{}:block-lists-clear".format(LinkDatabase.name))

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)

        lists = BlockEntryList.objects.all()
        self.assertFalse(lists.exists())


class BlockEntryViewsTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
            is_staff=True,
        )
        self.client.login(username="testuser", password="testpassword")

    def test_block_list_initialize(self):
        url = reverse("{}:block-entries".format(LinkDatabase.name))

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        entries = BlockEntry.objects.all()
        self.assertTrue(entries.exists())
