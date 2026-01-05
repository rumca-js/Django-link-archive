from django.urls import reverse
from django.contrib.auth.models import User

from utils.dateutils import DateUtils

from ..apps import LinkDatabase
from ..models import SearchView

from .fakeinternet import FakeInternetTestCase


class SearchViewTests(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser", password="testpassword", is_staff=True
        )

    def test_searchview_add__show_form(self):
        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:searchview-add".format(LinkDatabase.name), args=[])

        # call user action
        response = self.client.get(url)

        # redirect to view the link again
        self.assertEqual(response.status_code, 200)

    def test_searchview_edit__post(self):
        searchview = SearchView.objects.create()

        self.client.login(username="testuser", password="testpassword")

        url = reverse(
            "{}:searchview-edit".format(LinkDatabase.name), args=[searchview.id]
        )

        form_data = {
            "name": "",
            "default": False,
            "icon": "test",
            "order_by" : "test",
            "entry_limit": 200,
            "date_published_day_limit" : 5,
            "date_created_day_limit":5,
        }

        # call user action
        response = self.client.post(url, data=form_data)

        page_source = response.content.decode("utf-8")
        print("Contents: {}".format(page_source))
        print(response)

        self.assertEqual(response.status_code, 302)
