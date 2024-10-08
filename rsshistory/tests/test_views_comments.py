from django.urls import reverse
from django.contrib.auth.models import User

from utils.dateutils import DateUtils

from ..apps import LinkDatabase
from ..controllers import SourceDataController, LinkDataController, DomainsController
from ..models import KeyWords, DataExport, UserComments

from .fakeinternet import FakeInternetTestCase


class CommentsViewsTests(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
            is_staff=True,
        )

    def test_entry_comment_add(self):
        self.client.login(username="testuser", password="testpassword")

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

        self.assertEqual(UserComments.objects.all().count(), 0)

        url = reverse("{}:entry-comment-add".format(LinkDatabase.name), args=[entry.id])

        data = {"link": test_link}

        comment_data = {
            "entry_id": entry.id,
            "user_id": self.user.id,
            "user": self.user.username,
            "comment": "test comment",
            "date_published": DateUtils.get_datetime_now_utc(),
        }

        # call user action
        response = self.client.post(url, data=comment_data)

        # redirect to view the link again
        self.assertEqual(response.status_code, 302)

        # check that object has been changed

        entries = UserComments.objects.filter(entry=entry)
        self.assertEqual(entries.count(), 1)

    def test_entry_comment_edit(self):
        self.client.login(username="testuser", password="testpassword")

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

        UserComments.objects.create(entry=entry, user=self.user, comment="comment")

        url = reverse(
            "{}:entry-comment-edit".format(LinkDatabase.name), args=[entry.id]
        )

        data = {"link": test_link}

        comment_data = {
            "entry_id": entry.id,
            "user_id": self.user.id,
            "user": self.user.username,
            "comment": "test comment",
            "date_published": DateUtils.get_datetime_now_utc(),
        }

        # call user action
        response = self.client.post(url, data=comment_data)

        # redirect to view the link again
        self.assertEqual(response.status_code, 302)

        # check that object has been changed

        entries = UserComments.objects.filter(entry=entry)
        self.assertEqual(entries.count(), 1)

    def test_remove_comment(self):
        self.client.login(username="testuser", password="testpassword")

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

        UserComments.objects.create(entry=entry, user=self.user, comment="comment")

        url = reverse(
            "{}:entry-comment-remove".format(LinkDatabase.name), args=[entry.id]
        )

        # call user action
        response = self.client.post(url)

        # redirect to view the link again
        self.assertEqual(response.status_code, 200)

        entries = UserComments.objects.filter(entry=entry)
        self.assertEqual(entries.count(), 0)
