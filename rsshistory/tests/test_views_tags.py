from django.urls import reverse
from django.contrib.auth.models import User

from ..apps import LinkDatabase
from ..controllers import SourceDataController, LinkDataController, DomainsController
from ..dateutils import DateUtils
from ..models import KeyWords, DataExport, UserTags

from .fakeinternet import FakeInternetTestCase


class UserTagsTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser", password="testpassword", is_staff=True
        )

    def test_entry_tag(self):
        self.client.login(username="testuser", password="testpassword")

        test_link = "https://linkedin.com"

        entry = LinkDataController.objects.create(
            source="https://linkedin.com",
            link=test_link,
            title="The first link",
            description="the first link description",
            source_obj=None,
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        self.assertEqual(UserTags.objects.all().count(), 0)

        url = reverse("{}:entry-tag".format(LinkDatabase.name), args=[entry.id])

        tag_data = {
            "entry_id": entry.id,
            "user_id": self.user.id,
            "user": self.user.username,
            "tag": "this, and, that",
        }

        # call user action
        response = self.client.post(url, data=tag_data)

        # page_source = response.content.decode("utf-8")
        # print("Contents: {}".format(page_source))

        # redirect to view the link again
        self.assertEqual(response.status_code, 302)

        # check that object has been changed

        entries = UserTags.objects.filter(entry_object=entry)
        self.assertEqual(entries.count(), 3)

    def test_tag_remove(self):
        self.client.login(username="testuser", password="testpassword")

        entry = LinkDataController.objects.create(
            source="https://linkedin.com",
            link="https://linkedin.com/test",
            title="The first link",
            description="the first link description",
            source_obj=None,
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        tag = UserTags.objects.create(tag="personal", user_object=self.user, entry_object=entry)

        url = reverse("{}:tag-remove".format(LinkDatabase.name), args=[tag.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)

    def test_tag_entry_remove(self):
        self.client.login(username="testuser", password="testpassword")

        entry = LinkDataController.objects.create(
            source="https://linkedin.com",
            link="https://linkedin.com/test",
            title="The first link",
            description="the first link description",
            source_obj=None,
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        tag = UserTags.objects.create(tag="personal", user_object=self.user, entry_object=entry)

        url = reverse("{}:tags-entry-remove".format(LinkDatabase.name), args=[entry.id])
        response = self.client.get(url)

        page_source = response.content.decode("utf-8")
        print("Contents: {}".format(page_source))

        self.assertEqual(response.status_code, 302)

    def test_tag_entry_show(self):
        self.client.login(username="testuser", password="testpassword")

        entry = LinkDataController.objects.create(
            source="https://linkedin.com",
            link="https://linkedin.com/test",
            title="The first link",
            description="the first link description",
            source_obj=None,
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        tag = UserTags.objects.create(tag="personal", user_object=self.user, entry_object=entry)

        url = reverse("{}:tags-entry-show".format(LinkDatabase.name), args=[entry.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_tag_rename(self):
        self.client.login(username="testuser", password="testpassword")

        entry = LinkDataController.objects.create(
            source="https://linkedin.com",
            link="https://linkedin.com/test",
            title="The first link",
            description="the first link description",
            source_obj=None,
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        tag = UserTags.objects.create(tag="personal", user_object=self.user, entry_object=entry)

        url = reverse("{}:tag-rename".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_tag_show_all(self):

        entry = LinkDataController.objects.create(
            source="https://linkedin.com",
            link="https://linkedin.com/test",
            title="The first link",
            description="the first link description",
            source_obj=None,
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        tag = UserTags.objects.create(tag="personal", user_object=self.user, entry_object=entry)

        url = reverse("{}:tags-show-all".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_tag_show_recent(self):

        entry = LinkDataController.objects.create(
            source="https://linkedin.com",
            link="https://linkedin.com/test",
            title="The first link",
            description="the first link description",
            source_obj=None,
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        tag = UserTags.objects.create(tag="personal", user_object=self.user, entry_object=entry)

        url = reverse("{}:tags-show-recent".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
