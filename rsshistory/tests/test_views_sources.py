from django.urls import reverse
from django.contrib.auth.models import User

from ..apps import LinkDatabase
from ..controllers import SourceDataController, LinkDataController, DomainsController
from ..dateutils import DateUtils
from ..models import KeyWords, DataExport

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


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

        # print(response.text.decode('utf-8'))

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

        # print(response.text.decode('utf-8'))

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

        # print(response.text.decode('utf-8'))

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

        print(response.text.decode("utf-8"))

        # redirection
        self.assertEqual(response.status_code, 302)

        # check that object has been changed

        source = SourceDataController.objects.get(url=test_link)
        self.assertEqual(source.title, "LinkedIn Page title")


class SourceDetailTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )

        self.source_linkedin = SourceDataController.objects.create(
            url="https://linkedin.com",
            title="LinkedIn",
            category="No",
            subcategory="No",
            export_to_cms=False,
        )

        # entries for sources

        LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com",
            title="The first link",
            source_obj=self.source_youtube,
            bookmarked=False,
            permanent=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        self.entry_html = LinkDataController.objects.create(
            source="https://linkedin.com/feed",
            link="https://linkedin.com",
            title="The second link",
            source_obj=self.source_youtube,
            bookmarked=False,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        # other

        self.entry_youtube = LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=bookmarked",
            title="The first link",
            source_obj=self.source_youtube,
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=nonbookmarked",
            title="The second link",
            source_obj=self.source_youtube,
            bookmarked=False,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        self.entry_pdf = LinkDataController.objects.create(
            source="https://linkedin.com/feed",
            link="https://linkedin.com/link-to-pdf.pdf",
            title="The second link",
            source_obj=self.source_youtube,
            bookmarked=False,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
            is_staff=True,
        )
        self.client.login(username="testuser", password="testpassword")

    def test_source_detail_youtube(self):
        MockRequestCounter.mock_page_requests = 0
        url = reverse(
            "{}:source-detail".format(LinkDatabase.name),
            args=[self.source_youtube.id],
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_source_detail_html(self):
        MockRequestCounter.mock_page_requests = 0
        url = reverse(
            "{}:source-detail".format(LinkDatabase.name),
            args=[self.source_linkedin.id],
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # creates a link for that source
        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_source_json(self):
        MockRequestCounter.mock_page_requests = 0
        sources = SourceDataController.objects.filter(url__icontains="https://youtube")

        url = reverse("{}:source-json".format(LinkDatabase.name), args=[sources[0].id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_sources_json(self):
        sources = SourceDataController.objects.filter(url__icontains="https://youtube")

        url = reverse("{}:sources-json".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)


class SourceDetailTestCreatesEntries(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )

        self.source_linkedin = SourceDataController.objects.create(
            url="https://linkedin.com",
            title="LinkedIn",
            category="No",
            subcategory="No",
            export_to_cms=False,
        )

        # other

        self.entry_youtube = LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=bookmarked",
            title="The first link",
            source_obj=self.source_youtube,
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=nonbookmarked",
            title="The second link",
            source_obj=self.source_youtube,
            bookmarked=False,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        self.entry_pdf = LinkDataController.objects.create(
            source="https://linkedin.com/feed",
            link="https://linkedin.com/link-to-pdf.pdf",
            title="The second link",
            source_obj=self.source_youtube,
            bookmarked=False,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
            is_staff=True,
        )
        self.client.login(username="testuser", password="testpassword")

    def test_source_detail_youtube(self):
        MockRequestCounter.mock_page_requests = 0
        url = reverse(
            "{}:source-detail".format(LinkDatabase.name),
            args=[self.source_youtube.id],
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(MockRequestCounter.mock_page_requests, 1)

    def test_source_detail_html(self):
        MockRequestCounter.mock_page_requests = 0
        url = reverse(
            "{}:source-detail".format(LinkDatabase.name),
            args=[self.source_linkedin.id],
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # creates a link for that source
        self.assertEqual(MockRequestCounter.mock_page_requests, 1)
