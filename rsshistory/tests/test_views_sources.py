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
from ..models import (
    KeyWords,
    DataExport,
    SourceCategories,
    SourceSubCategories,
    SourceOperationalData,
    Browser,
)

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class SourcesViewsTests(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.user.is_staff = True
        self.user.save()

        # c = Configuration.get_object()
        # c.config_entry.logging_level = AppLogging.DEBUG
        # c.config_entry.save()

    def test_sources(self):
        SourceDataController.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:sources".format(LinkDatabase.name))

        # call user action
        response = self.client.get(url)

        # print(response.text.decode('utf-8'))

        self.assertEqual(response.status_code, 200)

    def test_source_add_simple(self):
        SourceDataController.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:source-add-simple".format(LinkDatabase.name))

        # call user action
        response = self.client.get(url)

        # print(response.text.decode('utf-8'))

        self.assertEqual(response.status_code, 200)

    def test_source_add__html(self):
        BackgroundJobController.objects.all().delete()
        SourceDataController.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:source-add".format(LinkDatabase.name))
        test_link = "https://linkedin.com"

        data = {"url": test_link}
        full_data = SourceDataController.get_full_information(data)
        full_data["enabled"] = True
        full_data["entries_backgroundcolor_alpha"] = 0.0
        full_data["entries_backgroundcolor"] = "#ffffff"
        full_data["entries_alpha"] = 1.0

        limited_data = {}
        for key in full_data:
            if full_data[key] is not None:
                limited_data[key] = full_data[key]

        print("Limited data")
        print(limited_data)

        self.assertEqual(BackgroundJobController.objects.all().count(), 0)
        self.assertEqual(SourceDataController.objects.filter(url=test_link).count(), 0)

        # call user action
        response = self.client.post(url, data=limited_data)

        # print(response.text.decode('utf-8'))

        self.assertEqual(response.status_code, 302)

        sources = SourceDataController.objects.filter(url=test_link)
        self.assertEqual(sources.count(), 1)
        source = sources[0]
        self.assertTrue(source.title != None)
        self.assertTrue(source.enabled)

        # entry for source is created via job
        self.assertEqual(
            BackgroundJobController.objects.filter(
                job=BackgroundJobController.JOB_PROCESS_SOURCE
            ).count(),
            1,
        )
        self.assertEqual(
            BackgroundJobController.objects.filter(
                job=BackgroundJobController.JOB_LINK_ADD
            ).count(),
            1,
        )

    def test_source_add__youtube(self):
        BackgroundJobController.objects.all().delete()
        SourceDataController.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:source-add".format(LinkDatabase.name))
        test_link = "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"

        data = {"url": test_link}
        full_data = SourceDataController.get_full_information(data)
        full_data["enabled"] = True
        full_data["entries_backgroundcolor_alpha"] = 0.0
        full_data["entries_backgroundcolor"] = "#ffffff"
        full_data["entries_alpha"] = 1.0

        limited_data = {}
        for key in full_data:
            if full_data[key] is not None:
                limited_data[key] = full_data[key]

        print("Limited data")
        print(limited_data)

        self.assertEqual(BackgroundJobController.objects.all().count(), 0)
        self.assertEqual(SourceDataController.objects.filter(url=test_link).count(), 0)

        # call user action
        response = self.client.post(url, data=limited_data)

        # print(response.text.decode('utf-8'))

        self.assertEqual(response.status_code, 302)

        sources = SourceDataController.objects.filter(url=test_link)
        self.assertEqual(sources.count(), 1)
        source = sources[0]
        self.assertTrue(source.title != None)
        self.assertTrue(source.enabled)

        # entry for source is created via job
        self.assertEqual(
            BackgroundJobController.objects.filter(
                job=BackgroundJobController.JOB_PROCESS_SOURCE
            ).count(),
            1,
        )
        self.assertEqual(
            BackgroundJobController.objects.filter(
                job=BackgroundJobController.JOB_LINK_ADD
            ).count(),
            1,
        )

    def test_source_add__odysee(self):
        BackgroundJobController.objects.all().delete()
        SourceDataController.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:source-add".format(LinkDatabase.name))
        test_link = "https://odysee.com/$/rss/@samtime:0"

        data = {"url": test_link}
        full_data = SourceDataController.get_full_information(data)
        full_data["enabled"] = True
        full_data["entries_backgroundcolor_alpha"] = 0.0
        full_data["entries_backgroundcolor"] = "#ffffff"
        full_data["entries_alpha"] = 1.0

        limited_data = {}
        for key in full_data:
            if full_data[key] is not None:
                limited_data[key] = full_data[key]

        print("Limited data")
        print(limited_data)

        self.assertEqual(BackgroundJobController.objects.all().count(), 0)
        self.assertEqual(SourceDataController.objects.filter(url=test_link).count(), 0)

        # call user action
        response = self.client.post(url, data=limited_data)

        # print(response.text.decode('utf-8'))

        self.assertEqual(response.status_code, 302)

        sources = SourceDataController.objects.filter(url=test_link)
        self.assertEqual(sources.count(), 1)
        source = sources[0]
        self.assertTrue(source.title != None)
        self.assertTrue(source.enabled)

        # entry for source is created via job
        self.assertEqual(
            BackgroundJobController.objects.filter(
                job=BackgroundJobController.JOB_PROCESS_SOURCE
            ).count(),
            1,
        )
        self.assertEqual(
            BackgroundJobController.objects.filter(
                job=BackgroundJobController.JOB_LINK_ADD
            ).count(),
            1,
        )

    def test_source_add__categories(self):
        BackgroundJobController.objects.all().delete()
        SourceDataController.objects.all().delete()
        SourceCategories.objects.all().delete()
        SourceSubCategories.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:source-add".format(LinkDatabase.name))
        test_link = "https://linkedin.com"

        data = {"url": test_link}
        full_data = SourceDataController.get_full_information(data)
        full_data["enabled"] = True
        full_data["category_name"] = "test1"
        full_data["subcategory_name"] = "test2"
        full_data["entries_backgroundcolor_alpha"] = 0.0
        full_data["entries_backgroundcolor"] = "#ffffff"
        full_data["entries_alpha"] = 1.0

        limited_data = {}
        for key in full_data:
            if full_data[key] is not None:
                limited_data[key] = full_data[key]

        print("Limited data")
        print(limited_data)

        # call user action
        response = self.client.post(url, data=limited_data)

        # print(response.text.decode('utf-8'))

        self.assertEqual(response.status_code, 302)

        sources = SourceDataController.objects.filter(url=test_link)
        self.assertEqual(sources.count(), 1)

        categories = SourceCategories.objects.all()
        self.assertEqual(categories.count(), 1)
        category = categories[0]
        self.assertEqual(category.name, "test1")

        subcategories = SourceSubCategories.objects.all()
        self.assertEqual(subcategories.count(), 1)
        subcategory = subcategories[0]
        self.assertEqual(subcategory.name, "test2")

    def test_source_add_form(self):
        LinkDataController.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:source-add-form".format(LinkDatabase.name))
        test_link = "https://linkedin.com"
        url = url + "?link=" + test_link

        # call user action
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_source_add_form__browser_empty(self):
        LinkDataController.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:source-add-form".format(LinkDatabase.name))
        test_link = "https://linkedin.com"
        url = url + "?link={}&browser={}".format(test_link, Browser.EMPTY_FORM)

        # call user action
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

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
        full_data["entries_backgroundcolor_alpha"] = 0.0
        full_data["entries_backgroundcolor"] = "#ffffff"
        full_data["entries_alpha"] = 1.0

        limited_data = {}
        for key in full_data:
            if full_data[key] is not None:
                limited_data[key] = full_data[key]

        print("Limited data")
        print(limited_data)

        # call user action
        response = self.client.post(url, data=limited_data)

        # redirection
        self.assertEqual(response.status_code, 302)

        # check that object has been changed

        source = SourceDataController.objects.get(url=test_link)
        self.assertEqual(source.title, "Https LinkedIn Page title")

    def test_source_remove__check_if_deps_removed(self):
        SourceDataController.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        test_link = "https://linkedin.com"

        source = SourceDataController.objects.create(
            url=test_link,
            title="The first link",
            language="en",
        )

        SourceOperationalData.objects.create(source_obj=source)

        BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_PROCESS_SOURCE, subject=str(source.id)
        )

        # call tested function
        url = reverse("{}:source-remove".format(LinkDatabase.name), args=[source.id])

        # call user action
        response = self.client.get(url)

        self.assertEqual(SourceDataController.objects.count(), 0)
        self.assertEqual(SourceOperationalData.objects.count(), 0)
        self.assertEqual(BackgroundJobController.objects.count(), 0)

    def test_sources_remove_all(self):
        SourceDataController.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        # call tested function
        url = reverse("{}:sources-remove-all".format(LinkDatabase.name))

        # call user action
        response = self.client.get(url)

        self.assertEqual(SourceDataController.objects.count(), 0)
        self.assertEqual(SourceOperationalData.objects.count(), 0)
        self.assertEqual(BackgroundJobController.objects.count(), 0)

    def test_sources_remove_disabled(self):
        SourceDataController.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        # call tested function
        url = reverse("{}:sources-remove-disabled".format(LinkDatabase.name))

        # call user action
        response = self.client.get(url)

        self.assertEqual(SourceDataController.objects.count(), 0)
        self.assertEqual(SourceOperationalData.objects.count(), 0)
        self.assertEqual(BackgroundJobController.objects.count(), 0)


class SourceDetailTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.source_youtube = SourceDataController.objects.create(
            url="https://www.youtube.com/channel/SAMTIMESAMTIMESAMTIMESAM",
            title="YouTube",
            category_name="No",
            subcategory_name="No",
            export_to_cms=True,
        )

        self.source_odysee = SourceDataController.objects.create(
            url="https://odysee.com/@samtime:1",
            title="Odysee",
            category_name="No",
            subcategory_name="No",
            export_to_cms=True,
        )

        self.source_linkedin = SourceDataController.objects.create(
            url="https://linkedin.com",
            title="LinkedIn",
            category_name="No",
            subcategory_name="No",
            export_to_cms=False,
        )

        # entries for sources

        LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com",
            title="The first link",
            source=self.source_youtube,
            bookmarked=False,
            permanent=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        self.entry_html = LinkDataController.objects.create(
            source_url="https://linkedin.com/feed",
            link="https://linkedin.com",
            title="The second link",
            source=self.source_youtube,
            bookmarked=False,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        # other

        self.entry_youtube = LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com/watch?v=bookmarked",
            title="The first link",
            source=self.source_youtube,
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com/watch?v=nonbookmarked",
            title="The second link",
            source=self.source_youtube,
            bookmarked=False,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        self.entry_pdf = LinkDataController.objects.create(
            source_url="https://linkedin.com/feed",
            link="https://linkedin.com/link-to-pdf.pdf",
            title="The second link",
            source=self.source_youtube,
            bookmarked=False,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        self.entry_odysee = LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://odysee.com/@samtime:1/apple-reacts-to-leaked-windows-12:1?test",
            title="The first link",
            source=self.source_youtube,
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
            is_staff=True,
        )
        self.client.login(username="testuser", password="testpassword")

    def test_source_detail__youtube_channel(self):
        MockRequestCounter.mock_page_requests = 0
        url = reverse(
            "{}:source-detail".format(LinkDatabase.name),
            args=[self.source_youtube.id],
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.no_errors())

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_source_detail__odysee(self):
        MockRequestCounter.mock_page_requests = 0
        url = reverse(
            "{}:source-detail".format(LinkDatabase.name),
            args=[self.source_odysee.id],
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.no_errors())

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_source_detail__html(self):
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
        sources = SourceDataController.objects.filter(
            url__icontains="https://www.youtube"
        )

        url = reverse("{}:source-json".format(LinkDatabase.name), args=[sources[0].id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_sources_json_all(self):
        sources = SourceDataController.objects.filter(
            url__icontains="https://www.youtube"
        )

        url = reverse("{}:sources-json-all".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_sources_json_enabled(self):
        sources = SourceDataController.objects.filter(
            url__icontains="https://www.youtube"
        )

        url = reverse("{}:sources-json-enabled".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)


class SourceDetailTestCreatesEntries(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category_name="No",
            subcategory_name="No",
            export_to_cms=True,
        )

        self.source_linkedin = SourceDataController.objects.create(
            url="https://linkedin.com",
            title="LinkedIn",
            category_name="No",
            subcategory_name="No",
            export_to_cms=False,
        )

        # other

        self.entry_youtube = LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=bookmarked",
            title="The first link",
            source=self.source_youtube,
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=nonbookmarked",
            title="The second link",
            source=self.source_youtube,
            bookmarked=False,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        self.entry_pdf = LinkDataController.objects.create(
            source_url="https://linkedin.com/feed",
            link="https://linkedin.com/link-to-pdf.pdf",
            title="The second link",
            source=self.source_youtube,
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

    def test_source_is__exists(self):
        MockRequestCounter.mock_page_requests = 0

        url = reverse("{}:source-is".format(LinkDatabase.name))

        url += "?link=https://linkedin.com"

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["status"])

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_source_is__does_not_exist(self):
        MockRequestCounter.mock_page_requests = 0

        url = reverse("{}:source-is".format(LinkDatabase.name))

        url += "?link=https://linkedin-does-not-exist.com"

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertFalse(data["status"])

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)
