from django.urls import reverse
from django.contrib.auth.models import User

from utils.dateutils import DateUtils

from ..apps import LinkDatabase
from ..models import SearchViews

from .fakeinternet import FakeInternetTestCase


class SearchViewTests(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser", password="testpassword", is_staff=True
        )

    def test_searchview_add__show_form(self):
        EntryRules.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:searchview-add".format(LinkDatabase.name), args=[])

        # call user action
        response = self.client.get(url)

        # redirect to view the link again
        self.assertEqual(response.status_code, 200)

    def test_entry_rule_edit__post(self):
        searchview = SearchView.objects.create(
        )

        self.client.login(username="testuser", password="testpassword")

        url = reverse(
            "{}:searchview-edit".format(LinkDatabase.name), args=[entry_rule.id]
        )

        form_data = {
            "enabled": False,
            "rule_name": "test_rule_edited",
            "trigger_text": "",
            "trigger_text_hits": 1,
            "trigger_text_fields": "",
        }

        # call user action
        response = self.client.post(url, data=form_data)

        self.assertEqual(response.status_code, 302)
