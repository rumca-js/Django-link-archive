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


class UserTagsTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser", password="testpassword", is_staff=True
        )

    def create_simple_entry(self):
        test_link = "https://linkedin.com"

        entry = LinkDataController.objects.create(
            source_url="https://linkedin.com",
            link=test_link,
            title="The first link",
            description="the first link description",
            source=None,
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        return entry

    def test_entry_tag(self):
        BackgroundJobController.objects.all().delete()
        UserTags.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        entry = self.create_simple_entry()

        url = reverse("{}:entry-tag".format(LinkDatabase.name), args=[entry.id])

        tag_data = {
            "entry_id": entry.id,
            "user_id": self.user.id,
            "user": self.user.username,
            "tags": "this, and, that",
        }

        # call user action
        response = self.client.post(url, data=tag_data)

        response_data = response.json()
        print(response_data["message"])

        # JSON tag
        self.assertEqual(response.status_code, 200)

        # check that object has been changed

        entries = UserTags.objects.filter(entry=entry)
        self.assertEqual(entries.count(), 3)

        # check that it removes old tags

        tag_data = {
            "entry_id": entry.id,
            "user_id": self.user.id,
            "user": self.user.username,
            "tags": "this",
        }

        # call user action
        response = self.client.post(url, data=tag_data)

        entries = UserTags.objects.filter(entry=entry)
        self.assertEqual(entries.count(), 1)

    def test_tag_remove(self):
        self.client.login(username="testuser", password="testpassword")

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

        tag = UserTags.objects.create(tag="personal", user=self.user, entry=entry)

        url = reverse("{}:tag-remove".format(LinkDatabase.name), args=[tag.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)

    def test_tag_entry_remove(self):
        self.client.login(username="testuser", password="testpassword")

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

        tag = UserTags.objects.create(tag="personal", user=self.user, entry=entry)

        url = reverse("{}:tags-entry-remove".format(LinkDatabase.name), args=[entry.id])
        response = self.client.get(url)

        # page_source = response.text.decode("utf-8")
        # print("Contents: {}".format(page_source))

        self.assertEqual(response.status_code, 302)

    def test_tag_entry_show(self):
        self.client.login(username="testuser", password="testpassword")

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

        tag = UserTags.objects.create(tag="personal", user=self.user, entry=entry)

        url = reverse("{}:entry-tags".format(LinkDatabase.name), args=[entry.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_tag_rename(self):
        self.client.login(username="testuser", password="testpassword")

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

        tag = UserTags.objects.create(tag="personal", user=self.user, entry=entry)

        url = reverse("{}:tag-rename".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_tag_show_all(self):
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

        tag = UserTags.objects.create(tag="personal", user=self.user, entry=entry)

        url = reverse("{}:tags-show-all".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_tag_show_actual(self):
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

        tag = UserTags.objects.create(tag="personal", user=self.user, entry=entry)

        url = reverse("{}:tags-show-actual".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_user_tags_show(self):
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

        tag = UserTags.objects.create(tag="personal", user=self.user, entry=entry)

        url = reverse("{}:user-tags-show".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
