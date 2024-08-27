from django.contrib.auth.models import User
from datetime import timedelta

from utils.dateutils import DateUtils

from ..controllers import (
    SourceDataController,
    LinkDataController,
    ArchiveLinkDataController,
    DomainsController,
)
from ..models import UserTags
from ..configuration import Configuration

from .fakeinternet import FakeInternetTestCase


class LinkDataControllerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="test_username", password="testpassword"
        )

    def clear(self):
        SourceDataController.objects.all().delete()
        LinkDataController.objects.all().delete()
        ArchiveLinkDataController.objects.all().delete()

    def create_entries(self, date_link_publish, date_to_remove):
        domain = DomainsController.objects.create(
            domain="https://youtube.com",
        )

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
            remove_after_days=1,
        )

        ob = LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=bookmarked",
            title="The first link",
            source_obj=source_youtube,
            bookmarked=True,
            language="en",
            domain_obj=domain,
            date_published=date_link_publish,
        )

        ob = LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=nonbookmarked",
            title="The second link",
            source_obj=source_youtube,
            bookmarked=False,
            language="en",
            domain_obj=domain,
            date_published=date_link_publish,
        )

        ob = LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=permanent",
            title="The first link",
            source_obj=source_youtube,
            permanent=True,
            language="en",
            domain_obj=domain,
            date_published=date_link_publish,
        )

        ob = ArchiveLinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=nonbookmarked2",
            title="The second link",
            source_obj=source_youtube,
            bookmarked=False,
            language="en",
            domain_obj=domain,
            date_published=date_to_remove,
        )

    def test_get_favicon_empty_in_model(self):
        conf = Configuration.get_object().config_entry

        current_time = DateUtils.get_datetime_now_utc()
        date_link_publish = current_time - timedelta(days=conf.days_to_remove_links + 2)
        date_to_remove = current_time - timedelta(days=conf.days_to_remove_links + 2)

        self.clear()
        self.create_entries(date_link_publish, date_to_remove)

        entries = LinkDataController.objects.filter(thumbnail__isnull=True)

        self.assertTrue(len(entries) != 0)
        # call tested function
        self.assertTrue(entries[0].get_favicon() == "https://youtube.com/favicon.ico")

    def test_get_thumbnail_empty_in_model(self):
        conf = Configuration.get_object().config_entry

        current_time = DateUtils.get_datetime_now_utc()
        date_link_publish = current_time - timedelta(days=conf.days_to_remove_links + 2)
        date_to_remove = current_time - timedelta(days=conf.days_to_remove_links + 2)

        self.clear()
        self.create_entries(date_link_publish, date_to_remove)

        entries = LinkDataController.objects.filter(thumbnail__isnull=True)

        self.assertTrue(len(entries) != 0)
        # call tested function
        self.assertEqual(entries[0].get_thumbnail(), "https://youtube.com/favicon.ico")

    def test_is_taggable_true(self):
        entry = LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=nonbookmarked",
            title="The second link",
            bookmarked=True,
            permanent=False,
            language="en",
            date_published=DateUtils.get_datetime_now_utc(),
        )

        self.assertTrue(entry.is_taggable())

    def test_is_taggable_false(self):
        entry = LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=nonbookmarked",
            title="The second link",
            bookmarked=False,
            permanent=False,
            language="en",
            date_published=DateUtils.get_datetime_now_utc(),
        )

        self.assertFalse(entry.is_taggable())

    def test_is_commentable_true(self):
        entry = LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=nonbookmarked",
            title="The second link",
            bookmarked=True,
            permanent=False,
            language="en",
            date_published=DateUtils.get_datetime_now_utc(),
        )

        self.assertTrue(entry.is_commentable())

    def test_is_commentable_false(self):
        entry = LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=nonbookmarked",
            title="The second link",
            bookmarked=False,
            permanent=False,
            language="en",
            date_published=DateUtils.get_datetime_now_utc(),
        )

        self.assertFalse(entry.is_commentable())

    def test_make_manual_dead(self):
        add_time = DateUtils.get_datetime_now_utc() - timedelta(days=1)

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
            remove_after_days=1,
        )

        entry = LinkDataController.objects.create(
            source="",
            link="https://linkedin.com",
            title="my title",
            description="my description",
            bookmarked=False,
            language="pl",
            domain_obj=None,
            date_published=add_time,
            thumbnail="thumbnail",
            source_obj=source_youtube,
        )

        date_updated = entry.date_update_last

        # call tested function
        entry.make_manual_dead()

        self.assertTrue(entry.date_dead_since is not None)
        self.assertEqual(entry.manual_status_code, 500)

    def test_make_manual_active(self):
        add_time = DateUtils.get_datetime_now_utc() - timedelta(days=1)

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
            remove_after_days=1,
        )

        entry = LinkDataController.objects.create(
            source="",
            link="https://linkedin.com",
            title="my title",
            description="my description",
            bookmarked=False,
            language="pl",
            domain_obj=None,
            date_published=add_time,
            thumbnail="thumbnail",
            source_obj=source_youtube,
            manual_status_code=0,
        )

        date_updated = entry.date_update_last

        # call tested function
        entry.make_manual_active()

        self.assertTrue(entry.date_dead_since is None)
        self.assertEqual(entry.manual_status_code, 200)

    def test_clear_manual_status(self):
        add_time = DateUtils.get_datetime_now_utc() - timedelta(days=1)

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
            remove_after_days=1,
        )

        entry = LinkDataController.objects.create(
            source="",
            link="https://linkedin.com",
            title="my title",
            description="my description",
            bookmarked=False,
            language="pl",
            domain_obj=None,
            date_published=add_time,
            thumbnail="thumbnail",
            source_obj=source_youtube,
            manual_status_code=200,
        )

        date_updated = entry.date_update_last

        # call tested function
        entry.clear_manual_status()

        self.assertTrue(entry.date_dead_since is None)
        self.assertEqual(entry.manual_status_code, 0)

    def test_is_https(self):
        entry_https = LinkDataController.objects.create(
            source="",
            link="https://linkedin.com",
            title="my title",
            description="my description",
            bookmarked=False,
            language="pl",
            domain_obj=None,
            thumbnail="thumbnail",
            manual_status_code=200,
        )

        entry_http = LinkDataController.objects.create(
            source="",
            link="http://linkedin.com",
            title="my title",
            description="my description",
            bookmarked=False,
            language="pl",
            domain_obj=None,
            thumbnail="thumbnail",
            manual_status_code=200,
        )

        # call tested function
        self.assertTrue(entry_https.is_https())
        self.assertFalse(entry_http.is_https())

    def test_is_http(self):
        entry_https = LinkDataController.objects.create(
            source="",
            link="https://linkedin.com",
            title="my title",
            description="my description",
            bookmarked=False,
            language="pl",
            domain_obj=None,
            thumbnail="thumbnail",
            manual_status_code=200,
        )

        entry_http = LinkDataController.objects.create(
            source="",
            link="http://linkedin.com",
            title="my title",
            description="my description",
            bookmarked=False,
            language="pl",
            domain_obj=None,
            thumbnail="thumbnail",
            manual_status_code=200,
        )

        # call tested function
        self.assertFalse(entry_https.is_http())
        self.assertTrue(entry_http.is_http())

    def test_get_tag_map(self):
        # demoted page
        entry = LinkDataController.objects.create(
            source="",
            link="https://linkedin.com",
            title="my title",
            description="my description",
            bookmarked=False,
            language="pl",
            domain_obj=None,
            thumbnail="thumbnail",
        )

        UserTags.objects.create(
            tag="test tag", user_object=self.user, entry_object=entry
        )

        tag_vec = entry.get_tag_map()
        self.assertEqual(len(tag_vec), 1)
        self.assertEqual(tag_vec[0], "test tag")

    def test_get_tag_map__invalid_page(self):
        # demoted page
        entry = LinkDataController.objects.create(
            source="",
            link="https://linkedin.com",
            title="my title",
            description="my description",
            bookmarked=False,
            language="pl",
            domain_obj=None,
            thumbnail="thumbnail",
            manual_status_code=200,
            date_dead_since=DateUtils.get_datetime_now_utc(),
            page_rating=-100,
            page_rating_contents=-100,
        )

        UserTags.objects.create(
            tag="test tag", user_object=self.user, entry_object=entry
        )

        tag_vec = entry.get_tag_map()
        self.assertEqual(len(tag_vec), 1)
        self.assertEqual(tag_vec[0], "test tag")

    def test_get_http_url(self):
        # demoted page
        entry = LinkDataController.objects.create(
            source="",
            link="https://linkedin.com",
            title="my title",
            description="my description",
            bookmarked=False,
            language="pl",
            domain_obj=None,
            thumbnail="thumbnail",
            manual_status_code=200,
            date_dead_since=DateUtils.get_datetime_now_utc(),
            page_rating=-100,
            page_rating_contents=-100,
        )

        # call tested function
        self.assertEqual(entry.get_http_url(), "http://linkedin.com")

    def test_get_https_url(self):
        # demoted page
        entry = LinkDataController.objects.create(
            source="",
            link="http://linkedin.com",
            title="my title",
            description="my description",
            bookmarked=False,
            language="pl",
            domain_obj=None,
            thumbnail="thumbnail",
            manual_status_code=200,
            date_dead_since=DateUtils.get_datetime_now_utc(),
            page_rating=-100,
            page_rating_contents=-100,
        )

        # call tested function
        self.assertEqual(entry.get_https_url(), "https://linkedin.com")
