from django.urls import reverse
from django.contrib.auth.models import User

from utils.dateutils import DateUtils

from ..apps import LinkDatabase
from ..controllers import SourceDataController, LinkDataController, DomainsController
from ..models import KeyWords, DataExport
from ..views import get_search_term, ViewPage

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class BasicViewTest(FakeInternetTestCase):
    """
    Tests most important aspects of display:
    header, footer, index
    """

    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
            is_staff=True,
        )
        self.client.login(username="testuser", password="testpassword")

    def test_index(self):
        url = reverse("{}:index".format(LinkDatabase.name))
        response = self.client.get(url)

        # redirect to search init
        self.assertEqual(response.status_code, 302)

    def test_get_footer_status_line(self):
        url = reverse("{}:get-footer-status-line".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_get_menu(self):
        url = reverse("{}:get-menu".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
