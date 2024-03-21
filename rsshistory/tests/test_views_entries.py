from django.urls import reverse
from django.contrib.auth.models import User

from ..apps import LinkDatabase
from ..controllers import (
    SourceDataController,
    LinkDataController,
    DomainsController,
    ArchiveLinkDataController,
    LinkDataBuilder,
)
from ..dateutils import DateUtils
from ..models import KeyWords, DataExport, UserBookmarks

from .fakeinternet import FakeInternetTestCase


class EntriesViewsTests(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser", password="testpassword", is_staff=True,
        )

    def get_link_data(self, test_link):
        data = {"link": test_link}

        full_data = LinkDataController.get_full_information(data)
        full_data["description"] = LinkDataController.get_description_safe(
            full_data["description"]
        )

        limited_data = {}
        for key in full_data:
            if full_data[key] is not None:
                limited_data[key] = full_data[key]

        return limited_data

    def test_add_simple_entry(self):
        LinkDataController.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:entry-add-simple".format(LinkDatabase.name))
        test_link = "https://linkedin.com"

        post_data = {"link": test_link}

        # call user action
        response = self.client.post(url, data=post_data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, test_link, html=False)

    def test_add_entry_html(self):
        LinkDataController.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:entry-add".format(LinkDatabase.name))
        test_link = "https://linkedin.com"

        limited_data = self.get_link_data(test_link)

        self.assertEqual(LinkDataController.objects.filter(link=test_link).count(), 0)

        # call user action
        response = self.client.post(url, data=limited_data)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(LinkDataController.objects.filter(link=test_link).count(), 1)

        bookmarks = UserBookmarks.get_user_bookmarks(self.user)
        self.assertEqual(bookmarks.count(), 0)

    def test_add_entry_rss(self):
        LinkDataController.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:entry-add".format(LinkDatabase.name))
        test_link = "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"

        limited_data = self.get_link_data(test_link)

        self.assertEqual(LinkDataController.objects.filter(link=test_link).count(), 0)

        # call user action
        response = self.client.post(url, data=limited_data)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(LinkDataController.objects.filter(link=test_link).count(), 1)

    def test_add_entry_exists(self):
        LinkDataController.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:entry-add".format(LinkDatabase.name))
        test_link = "https://linkedin.com"

        LinkDataBuilder(link=test_link)

        limited_data = self.get_link_data(test_link)

        self.assertEqual(LinkDataController.objects.filter(link=test_link).count(), 1)

        # call user action
        response = self.client.post(url, data=limited_data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(LinkDataController.objects.filter(link=test_link).count(), 1)

    def test_add_entry_exists_in_archive(self):
        LinkDataController.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:entry-add".format(LinkDatabase.name))
        test_link = "https://linkedin.com"

        ob = ArchiveLinkDataController.objects.create(
            source="https://linkin.com",
            link=test_link,
            title="The second link",
            language="en",
            date_published=DateUtils.get_datetime_now_utc(),
        )

        limited_data = self.get_link_data(test_link)

        self.assertEqual(
            ArchiveLinkDataController.objects.filter(link=test_link).count(), 1
        )
        self.assertEqual(LinkDataController.objects.filter(link=test_link).count(), 0)

        # call user action
        response = self.client.post(url, data=limited_data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            ArchiveLinkDataController.objects.filter(link=test_link).count(), 1
        )
        self.assertEqual(LinkDataController.objects.filter(link=test_link).count(), 0)

    def test_add_entry_bookmarked(self):
        LinkDataController.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:entry-add".format(LinkDatabase.name))
        test_link = "https://linkedin.com"

        limited_data = self.get_link_data(test_link)
        limited_data["bookmarked"] = True

        self.assertEqual(LinkDataController.objects.filter(link=test_link).count(), 0)

        # call user action
        response = self.client.post(url, data=limited_data)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(LinkDataController.objects.filter(link=test_link).count(), 1)

        bookmarks = UserBookmarks.get_user_bookmarks(self.user)
        self.assertEqual(bookmarks.count(), 1)

    def test_edit_entry(self):
        LinkDataController.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        test_link = "https://linkedin.com"

        entry = LinkDataController.objects.create(
            source="https://linkedin.com",
            link=test_link,
            title="The first link",
            description="the first link description",
            source_obj=None,
            bookmarked=False,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        url = reverse("{}:entry-edit".format(LinkDatabase.name), args=[entry.id])

        limited_data = self.get_link_data(test_link)

        # call user action
        response = self.client.post(url, data=limited_data)

        # redirection
        self.assertEqual(response.status_code, 302)

        # check that object has been changed

        entry = LinkDataController.objects.get(link=test_link)
        self.assertEqual(entry.title, "LinkedIn Page title")
        self.assertEqual(entry.description, "LinkedIn Page description")

        bookmarks = UserBookmarks.get_user_bookmarks(self.user)
        self.assertEqual(bookmarks.count(), 0)

    def test_edit_entry_bookmarked(self):
        LinkDataController.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        test_link = "https://linkedin.com"

        entry = LinkDataController.objects.create(
            source="https://linkedin.com",
            link=test_link,
            title="The first link",
            description="the first link description",
            source_obj=None,
            bookmarked=False,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        url = reverse("{}:entry-edit".format(LinkDatabase.name), args=[entry.id])

        limited_data = self.get_link_data(test_link)
        limited_data["bookmarked"] = True

        # call user action
        response = self.client.post(url, data=limited_data)

        # redirection
        self.assertEqual(response.status_code, 302)

        # check that object has been changed

        entry = LinkDataController.objects.get(link=test_link)
        self.assertEqual(entry.title, "LinkedIn Page title")
        self.assertEqual(entry.description, "LinkedIn Page description")

        bookmarks = UserBookmarks.get_user_bookmarks(self.user)
        self.assertEqual(bookmarks.count(), 1)

    def test_entry_download(self):
        LinkDataController.objects.all().delete()

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

        url = reverse("{}:entry-download".format(LinkDatabase.name), args=[entry.id])

        # call user action
        response = self.client.get(url)

    def test_entry_download_music(self):
        LinkDataController.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        test_link = "https://www.youtube.com/watch?v=123"

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

        url = reverse(
            "{}:entry-download-music".format(LinkDatabase.name), args=[entry.id]
        )

        # call user action
        response = self.client.get(url)

    def test_entry_download_video(self):
        LinkDataController.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        test_link = "https://www.youtube.com/watch?v=123"

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

        url = reverse(
            "{}:entry-download-video".format(LinkDatabase.name), args=[entry.id]
        )

        # call user action
        response = self.client.get(url)
