from django.urls import reverse
from django.contrib.auth.models import User

from ..apps import LinkDatabase
from ..controllers import SourceDataController, LinkDataController, DomainsController
from ..dateutils import DateUtils
from ..models import KeyWords, DataExport, UserVotes

from .fakeinternet import FakeInternetTestCase


class UserVotesTests(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.user.is_staff = True
        self.user.save()

    def test_add_vote(self):
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

        self.assertEqual(UserVotes.objects.all().count(), 0)

        url = reverse("{}:entry-vote".format(LinkDatabase.name), args=[entry.id])

        data = {"link": test_link}

        vote_data = {
            "entry_id": entry.id,
            "user_id": self.user.id,
            "user": self.user.username,
            "vote": "30",
        }

        # call user action
        response = self.client.post(url, data=vote_data)

        # redirect to view the link again
        self.assertEqual(response.status_code, 302)

        # check that object has been changed

        entries = UserVotes.objects.filter(entry_object=entry)
        self.assertEqual(entries.count(), 1)
