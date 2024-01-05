from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User

from ..apps import LinkDatabase
from ..controllers import SourceDataController, LinkDataController, DomainsController
from ..dateutils import DateUtils
from ..models import KeyWords, DataExport

from .utilities import WebPageDisabled


class PostViewTests(WebPageDisabled, TestCase):
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

        response = self.client.post(url, data=limited_data)

        self.assertEqual(response.status_code, 200)
