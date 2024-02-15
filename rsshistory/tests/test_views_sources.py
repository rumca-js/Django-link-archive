from django.urls import reverse
from django.contrib.auth.models import User

from ..apps import LinkDatabase
from ..controllers import SourceDataController, LinkDataController, DomainsController
from ..dateutils import DateUtils
from ..models import KeyWords, DataExport

from .fakeinternet import FakeInternetTestCase


class SourcesViewsTests(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.user.is_staff = True
        self.user.save()

    def test_add_simple_source(self):
        SourceDataController.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:source-add-simple".format(LinkDatabase.name))
        test_link = "https://linkedin.com"

        post_data = {"url": test_link}

        # call user action
        response = self.client.post(url, data=post_data)

        # print(response.content.decode('utf-8'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, test_link, html=False)

    def test_add_source_html(self):
        SourceDataController.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:source-add".format(LinkDatabase.name))
        test_link = "https://linkedin.com"

        data = {"url": test_link}
        full_data = SourceDataController.get_full_information(data)

        limited_data = {}
        for key in full_data:
            if full_data[key] is not None:
                limited_data[key] = full_data[key]

        print("Limited data")
        print(limited_data)

        self.assertEqual(SourceDataController.objects.filter(url=test_link).count(), 0)

        # call user action
        response = self.client.post(url, data=limited_data)

        # print(response.content.decode('utf-8'))

        self.assertEqual(response.status_code, 302)

        self.assertEqual(SourceDataController.objects.filter(url=test_link).count(), 1)

    def test_add_source_rss(self):
        SourceDataController.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:source-add".format(LinkDatabase.name))
        test_link = "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"

        data = {"url": test_link}
        full_data = SourceDataController.get_full_information(data)

        limited_data = {}
        for key in full_data:
            if full_data[key] is not None:
                limited_data[key] = full_data[key]

        print("Limited data")
        print(limited_data)

        self.assertEqual(SourceDataController.objects.filter(url=test_link).count(), 0)

        # call user action
        response = self.client.post(url, data=limited_data)

        # print(response.content.decode('utf-8'))

        self.assertEqual(response.status_code, 302)

        self.assertEqual(SourceDataController.objects.filter(url=test_link).count(), 1)

    def test_edit_source(self):
        SourceDataController.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        test_link = "https://linkedin.com"

        source = SourceDataController.objects.create(
            url=test_link,
            title="The first link",
            language="en",
        )
        self.assertEqual(SourceDataController.objects.filter(url=test_link).count(), 1)

        url = reverse("{}:source-edit".format(LinkDatabase.name), args=[source.id])

        data = {"url": test_link}
        full_data = SourceDataController.get_full_information(data)

        limited_data = {}
        for key in full_data:
            if full_data[key] is not None:
                limited_data[key] = full_data[key]

        print("Limited data")
        print(limited_data)

        # call user action
        response = self.client.post(url, data=limited_data)

        print(response.content.decode("utf-8"))

        # redirection
        self.assertEqual(response.status_code, 302)

        # check that object has been changed

        source = SourceDataController.objects.get(url=test_link)
        self.assertEqual(source.title, "LinkedIn Page title")
