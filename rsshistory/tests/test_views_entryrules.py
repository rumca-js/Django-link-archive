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
from ..models import EntryRules

from .fakeinternet import FakeInternetTestCase


class EntryRulesTests(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser", password="testpassword", is_staff=True
        )

    def test_entry_rule_add_form(self):
        EntryRules.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:entry-rule-add".format(LinkDatabase.name), args=[])

        # call user action
        response = self.client.get(url)

        # redirect to view the link again
        self.assertEqual(response.status_code, 200)

    def test_entry_rule_add_form(self):
        EntryRules.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:entry-rule-add".format(LinkDatabase.name), args=[])

        form_data = {
            "enabled": "False",
            "rule_name": "test_rule_edited",
        }

        # call user action
        response = self.client.post(url, data=form_data)

        self.assertEqual(response.status_code, 200)

    def test_entry_rule_edit(self):
        entry_rule = EntryRules.objects.create(
            enabled=True,
            rule_name="test_rule",
            rule_url="https://neocities.com",
            auto_tag="personal",
        )

        self.client.login(username="testuser", password="testpassword")

        url = reverse(
            "{}:entry-rule-edit".format(LinkDatabase.name), args=[entry_rule.id]
        )

        form_data = {
            "enabled": False,
            "rule_name": "test_rule_edited",
        }

        # call user action
        response = self.client.post(url, data=form_data)

        self.assertEqual(response.status_code, 200)

    def test_entry_rule_remove(self):
        entry_rule = EntryRules.objects.create(
            enabled=True,
            rule_name="test_rule",
            rule_url="https://neocities.com",
            auto_tag="personal",
        )

        self.client.login(username="testuser", password="testpassword")

        url = reverse(
            "{}:entry-rule-remove".format(LinkDatabase.name), args=[entry_rule.id]
        )

        # call user action
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)

        self.assertEqual(EntryRules.objects.all().count(), 0)

    def test_entry_rule_list(self):
        entry_rule = EntryRules.objects.create(
            enabled=True,
            rule_name="test_rule",
            rule_url="https://neocities.com",
            auto_tag="personal",
        )

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:entry-rules".format(LinkDatabase.name), args=[])

        # call user action
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_entry_rule_detail(self):
        entry_rule = EntryRules.objects.create(
            enabled=True,
            rule_name="test_rule",
            rule_url="https://neocities.com",
            auto_tag="personal",
        )

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:entry-rule".format(LinkDatabase.name), args=[entry_rule.id])

        # call user action
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_entry_rule_json(self):
        entry_rule = EntryRules.objects.create(
            enabled=True,
            rule_name="test_rule",
            rule_url="https://neocities.com",
            auto_tag="personal",
        )

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:entry-rules-json".format(LinkDatabase.name))

        # call user action
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
