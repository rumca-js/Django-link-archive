from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User

from ..apps import LinkDatabase
from ..controllers import SourceDataController, LinkDataController, DomainsController
from ..dateutils import DateUtils
from ..models import KeyWords, DataExport

from .utilities import WebPageDisabled


class EntriesViewsTests(WebPageDisabled, TestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.user.is_staff = True
        self.user.save()

    def test_add_simple_entry(self):
        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:entry-add-simple".format(LinkDatabase.name))
        test_link = "https://linkedin.com"

        post_data = {"link": test_link}

        # call user action
        response = self.client.post(url, data=post_data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, test_link, html=False)

    def test_add_entry(self):
        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:entry-add".format(LinkDatabase.name))
        test_link = "https://linkedin.com"

        data = {"link": test_link}
        full_data = LinkDataController.get_full_information(data)

        limited_data = {}
        for key in full_data:
            if full_data[key] is not None:
                limited_data[key] = full_data[key]

        self.assertEqual(LinkDataController.objects.filter(link=test_link).count(), 0)

        # call user action
        response = self.client.post(url, data=limited_data)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(LinkDataController.objects.filter(link=test_link).count(), 1)

    def test_edit_entry(self):
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

        url = reverse("{}:entry-edit".format(LinkDatabase.name), args=[entry.id])

        data = {"link": test_link}
        full_data = LinkDataController.get_full_information(data)

        limited_data = {}
        for key in full_data:
            if full_data[key] is not None:
                limited_data[key] = full_data[key]
        limited_data["date_published"] = "2020-03-03;16:34"
        print("Limited data: {}".format(limited_data))

        # call user action
        response = self.client.post(url, data=limited_data)

        # redirection
        self.assertEqual(response.status_code, 302)

        # check that object has been changed

        entry = LinkDataController.objects.get(link=test_link)
        self.assertEqual(entry.title, "LinkedIn Page title")
        self.assertEqual(entry.description, "LinkedIn Page description")
