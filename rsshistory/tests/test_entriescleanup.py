from datetime import timedelta
from django.contrib.auth.models import User

from ..models import UserBookmarks
from ..controllers import (
    LinkDataWrapper,
    SourceDataController,
    DomainsController,
    EntriesCleanup,
)
from ..controllers import LinkDataController, ArchiveLinkDataController
from ..dateutils import DateUtils
from ..configuration import Configuration

from .fakeinternet import FakeInternetTestCase, DjangoRequestObject


class EntriesCleanupTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )

        self.user_staff = User.objects.create_user(
            username="TestUser", password="testpassword", is_staff=True
        )
        self.user_not_staff = User.objects.create_user(
            username="TestUserNot", password="testpassword", is_staff=False
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

    def test_cleanup_old_entries_operational(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_remove_links = 2
        conf.save()

        current_time = DateUtils.get_datetime_now_utc()
        date_link_publish = current_time - timedelta(days=conf.days_to_remove_links + 2)
        date_to_remove = current_time - timedelta(days=conf.days_to_remove_links + 2)

        self.clear()
        self.create_entries(date_link_publish, date_to_remove)

        # call tested function
        EntriesCleanup().cleanup()

        bookmarked = LinkDataController.objects.filter(
            link="https://youtube.com?v=bookmarked"
        )
        self.assertEqual(bookmarked.count(), 1)

        permanent = LinkDataController.objects.filter(
            link="https://youtube.com?v=permanent"
        )
        self.assertEqual(permanent.count(), 1)

        nonbookmarked = LinkDataController.objects.filter(
            link="https://youtube.com?v=nonbookmarked"
        )
        self.assertEqual(nonbookmarked.count(), 0)

        self.assertEqual(ArchiveLinkDataController.objects.all().count(), 1)

    def test_cleanup__old_entries_archive(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_remove_links = 2
        conf.save()

        current_time = DateUtils.get_datetime_now_utc()
        date_link_publish = current_time - timedelta(days=conf.days_to_remove_links + 2)
        date_to_remove = current_time - timedelta(days=conf.days_to_remove_links + 2)

        self.clear()
        self.create_entries(date_link_publish, date_to_remove)

        # call tested function
        EntriesCleanup(archive_cleanup=True).cleanup()

        bookmarked = LinkDataController.objects.filter(
            link="https://youtube.com?v=bookmarked"
        )
        self.assertEqual(bookmarked.count(), 1)

        permanent = LinkDataController.objects.filter(
            link="https://youtube.com?v=permanent"
        )
        self.assertEqual(permanent.count(), 1)

        nonbookmarked = LinkDataController.objects.filter(
            link="https://youtube.com?v=nonbookmarked"
        )
        self.assertEqual(nonbookmarked.count(), 1)

        self.assertEqual(ArchiveLinkDataController.objects.all().count(), 0)

    def test_cleanup__https_http_duplicates(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_remove_links = 2
        conf.save()

        current_time = DateUtils.get_datetime_now_utc()
        date_link_publish = current_time - timedelta(days=conf.days_to_remove_links + 2)
        date_to_remove = current_time - timedelta(days=conf.days_to_remove_links + 2)

        self.clear()

        ob = LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=permanent",
            title="The first link",
            permanent=True,
            language="en",
        )

        ob = LinkDataController.objects.create(
            source="http://youtube.com",
            link="http://youtube.com?v=permanent",
            title="The second link",
            permanent=True,
            language="en",
        )

        # call tested function
        EntriesCleanup().cleanup()

        self.assertEqual(LinkDataController.objects.all().count(), 1)
