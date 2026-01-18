from django.urls import reverse
from django.contrib.auth.models import User

from utils.dateutils import DateUtils

from ..apps import LinkDatabase
from ..models import Browser
from ..controllers import (
    LinkDataController,
    BackgroundJobController,
)

from .fakeinternet import FakeInternetTestCase


class BrowserViewsTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser", password="testpassword", is_staff=True
        )

    def test_browsers(self):
        Browser.objects.create(name="Test")

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:browsers".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_browser_add(self):
        Browser.objects.create(name="Test")

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:browser-add".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_browser_disable(self):
        browser = Browser.objects.create(name="Test", enabled=True)

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:browser-disable".format(LinkDatabase.name), args=[browser.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)

    def test_browser_enable(self):
        browser = Browser.objects.create(name="Test", enabled=False)

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:browser-enable".format(LinkDatabase.name), args=[browser.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)

    def test_browser_edit(self):
        browser = Browser.objects.create(name="Test", enabled=False)

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:browser-edit".format(LinkDatabase.name), args=[browser.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_browser_prio_up__bump_to_rest(self):
        browser1 = Browser.objects.create(name="Test1", enabled=True, priority=1)
        browser2 = Browser.objects.create(name="Test2", enabled=True, priority=3)
        browser3 = Browser.objects.create(name="Test3", enabled=True, priority=5)

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:browser-prio-up".format(LinkDatabase.name), args=[browser3.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(browser1.priority, 1)
        self.assertEqual(browser2.priority, 3)
        self.assertEqual(browser3.priority, 2)
