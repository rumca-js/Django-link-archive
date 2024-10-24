from django.urls import reverse
from django.contrib.auth.models import User

from utils.dateutils import DateUtils

from ..apps import LinkDatabase
from ..controllers import (
    SourceDataController,
    LinkDataController,
)
from ..models import (
   UserSearchHistory
)

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class UserHistoryViewsTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
            is_staff=True,
        )

        self.source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
        )

        self.source_linkedin = SourceDataController.objects.create(
            url="https://linkedin.com",
            title="LinkedIn",
        )

        self.entry_youtube = LinkDataController.objects.create(
            link="https://youtube.com?v=bookmarked",
            title="The first link",
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
        )

        self.entry_linkedin = LinkDataController.objects.create(
            link="https://linkedin.com?v=bookmarked",
            title="The first link",
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
        )

        #self.user = User.objects.create_user(
        #    username="testuser", password="testpassword",)

        self.client.login(username="testuser", password="testpassword")

    def test_get_search_suggestions__search_history(self):
        history = UserSearchHistory.objects.create(search_query = "lolipop", user=self.user)

        url = reverse("{}:get-search-suggestions".format(LinkDatabase.name), args=["lolipop"])

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # Parse the JSON response
        data = response.json()

        # Check if 'items' is in the response and its length is > 0
        self.assertIn('items', data)
        self.assertTrue(len(data['items']) > 0, "Items list should not be empty.")
        self.assertEqual(data['items'][0], "lolipop")

    def test_get_search_suggestions__sources(self):
        history = UserSearchHistory.objects.create(search_query = "lolipop", user=self.user)

        url = reverse("{}:get-search-suggestions".format(LinkDatabase.name), args=["youtube"])

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # Parse the JSON response
        data = response.json()

        # Check if 'items' is in the response and its length is > 0
        self.assertIn('items', data)
        self.assertTrue(len(data['items']) > 0, "Items list should not be empty.")
        self.assertEqual(data['items'][0], "source__title = 'YouTube'")
