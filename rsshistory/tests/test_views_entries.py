from django.urls import reverse
from django.contrib.auth.models import User

from ..apps import LinkDatabase
from ..controllers import (
    SourceDataController,
    LinkDataController,
    DomainsController,
    ArchiveLinkDataController,
    EntryDataBuilder,
)
from ..dateutils import DateUtils
from ..models import KeyWords, DataExport, UserBookmarks

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class EntriesViewsTests(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
            is_staff=True,
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

        EntryDataBuilder(link=test_link)

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

    def test_entry_bookmark(self):
        test_link = "https://www.youtube.com/watch?v=123"

        entry = LinkDataController.objects.create(
            source="https://linkedin.com",
            link=test_link,
            title="The first link",
            description="the first link description",
            source_obj=None,
            bookmarked=False,
            permanent=False,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        self.client.login(username="testuser", password="testpassword")
        url = reverse("{}:entry-bookmark".format(LinkDatabase.name), args=[entry.id])

        # call user action
        response = self.client.get(url)
        print(url)

        entry.refresh_from_db()

        # page_source = response.text.decode("utf-8")
        # print("Contents: {}".format(page_source))
        # print(response)

        self.assertEqual(response.status_code, 302)

        self.assertTrue(entry.bookmarked)
        self.assertFalse(entry.permanent)

        bookmarks = UserBookmarks.objects.filter(entry_object=entry)
        self.assertEqual(bookmarks.count(), 1)

    def test_entry_notbookmark(self):
        test_link = "https://www.youtube.com/watch?v=123"

        entry = LinkDataController.objects.create(
            source="https://linkedin.com",
            link=test_link,
            title="The first link",
            description="the first link description",
            source_obj=None,
            bookmarked=True,
            permanent=False,
            date_published=DateUtils.get_datetime_now_utc(),
            language="en",
        )

        UserBookmarks.objects.create(entry_object=entry, user_object=self.user)

        self.client.login(username="testuser", password="testpassword")
        url = reverse("{}:entry-notbookmark".format(LinkDatabase.name), args=[entry.id])

        # call user action
        response = self.client.get(url)

        entry.refresh_from_db()

        # page_source = response.text.decode("utf-8")
        # print("Contents: {}".format(page_source))

        self.assertEqual(response.status_code, 302)

        self.assertFalse(entry.bookmarked)
        self.assertFalse(entry.permanent)

        bookmarks = UserBookmarks.objects.filter(entry_object=entry)
        self.assertEqual(bookmarks.count(), 0)

    def test_archive_entry_bookmark(self):
        test_link = "https://www.youtube.com/watch?v=123"

        entry = ArchiveLinkDataController.objects.create(
            source="https://linkedin.com",
            link=test_link,
            title="The first link",
            description="the first link description",
            source_obj=None,
            bookmarked=False,
            permanent=False,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        self.client.login(username="testuser", password="testpassword")
        url = reverse(
            "{}:entry-archive-bookmark".format(LinkDatabase.name), args=[entry.id]
        )

        # call user action
        response = self.client.get(url)

        # page_source = response.text.decode("utf-8")
        # print("Contents: {}".format(page_source))
        # print(response)

        self.assertEqual(response.status_code, 302)

        entries = LinkDataController.objects.filter(link=test_link)
        self.assertTrue(entries.count() > 0)

        entry = entries[0]

        self.assertTrue(entry.bookmarked)
        self.assertFalse(entry.permanent)

        bookmarks = UserBookmarks.objects.filter(entry_object=entry)
        self.assertEqual(bookmarks.count(), 1)

    def test_entry_active(self):
        test_link = "https://www.youtube.com/watch?v=123"

        entry = LinkDataController.objects.create(
            source="https://linkedin.com",
            link=test_link,
            title="The first link",
            description="the first link description",
            source_obj=None,
            bookmarked=True,
            permanent=False,
            date_published=DateUtils.get_datetime_now_utc(),
            date_dead_since=DateUtils.get_datetime_now_utc(),
            language="en",
        )

        self.client.login(username="testuser", password="testpassword")
        url = reverse("{}:entry-active".format(LinkDatabase.name), args=[entry.id])
        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)

        entry.refresh_from_db()
        self.assertEqual(entry.manual_status_code, LinkDataController.STATUS_ACTIVE)

    def test_entry_dead(self):
        test_link = "https://www.youtube.com/watch?v=123"

        entry = LinkDataController.objects.create(
            source="https://linkedin.com",
            link=test_link,
            title="The first link",
            description="the first link description",
            source_obj=None,
            bookmarked=True,
            permanent=False,
            date_published=DateUtils.get_datetime_now_utc(),
            language="en",
        )

        self.client.login(username="testuser", password="testpassword")
        url = reverse("{}:entry-dead".format(LinkDatabase.name), args=[entry.id])
        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)

        entry.refresh_from_db()
        self.assertEqual(entry.manual_status_code, LinkDataController.STATUS_DEAD)

    def test_entry_clear_status(self):
        test_link = "https://www.youtube.com/watch?v=123"

        entry = LinkDataController.objects.create(
            source="https://linkedin.com",
            link=test_link,
            title="The first link",
            description="the first link description",
            source_obj=None,
            bookmarked=True,
            permanent=False,
            date_published=DateUtils.get_datetime_now_utc(),
            language="en",
            manual_status_code=LinkDataController.STATUS_DEAD,
        )

        self.client.login(username="testuser", password="testpassword")
        url = reverse(
            "{}:entry-clear-status".format(LinkDatabase.name), args=[entry.id]
        )
        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)

        entry.refresh_from_db()
        self.assertEqual(entry.manual_status_code, LinkDataController.STATUS_UNDEFINED)


class EntriesViewsTests2(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )
        self.entry_youtube = LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=bookmarked",
            title="The first link",
            source_obj=source_youtube,
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=nonbookmarked",
            title="The second link",
            source_obj=source_youtube,
            bookmarked=False,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        self.entry_html = LinkDataController.objects.create(
            source="https://linkedin.com/feed",
            link="https://linkedin.com",
            title="The second link",
            source_obj=source_youtube,
            bookmarked=False,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        self.entry_pdf = LinkDataController.objects.create(
            source="https://linkedin.com/feed",
            link="https://linkedin.com/link-to-pdf.pdf",
            title="The second link",
            source_obj=source_youtube,
            bookmarked=False,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        SourceDataController.objects.create(
            url="https://linkedin.com",
            title="LinkedIn",
            category="No",
            subcategory="No",
            export_to_cms=False,
        )

        domain = DomainsController.objects.create(
            domain="https://youtube.com",
        )
        domain.date_created = DateUtils.from_string(
            "2023-03-03;16:34", "%Y-%m-%d;%H:%M"
        )
        domain.save()

        keyword = KeyWords.objects.create(keyword="test")

        self.export_daily = DataExport.objects.create(
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_DAILY_DATA,
            local_path=".",
            remote_path=".",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=True,
            export_sources=True,
        )

        self.export_year = DataExport.objects.create(
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_YEAR_DATA,
            local_path=".",
            remote_path=".",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=True,
            export_sources=True,
        )

        self.export_notime = DataExport.objects.create(
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_NOTIME_DATA,
            local_path=".",
            remote_path=".",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=True,
            export_sources=True,
        )

        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
            is_staff=True,
        )
        self.client.login(username="testuser", password="testpassword")

    def test_entry_detail_youtube(self):
        MockRequestCounter.mock_page_requests = 0

        url = reverse(
            "{}:entry-detail".format(LinkDatabase.name),
            args=[self.entry_youtube.id],
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_entry_detail_html(self):
        MockRequestCounter.mock_page_requests = 0

        url = reverse(
            "{}:entry-detail".format(LinkDatabase.name),
            args=[self.entry_html.id],
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_entry_detail_pdf(self):
        MockRequestCounter.mock_page_requests = 0

        url = reverse(
            "{}:entry-detail".format(LinkDatabase.name),
            args=[self.entry_pdf.id],
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_entry_json(self):
        MockRequestCounter.mock_page_requests = 0
        entries = LinkDataController.objects.filter(link__icontains="https://youtube")

        url = reverse("{}:entry-json".format(LinkDatabase.name), args=[entries[0].id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_entries_json(self):
        MockRequestCounter.mock_page_requests = 0
        entries = LinkDataController.objects.filter(link__icontains="https://youtube")

        url = reverse("{}:entries-json".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(MockRequestCounter.mock_page_requests, 0)
