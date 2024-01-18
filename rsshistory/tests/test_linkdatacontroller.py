from datetime import timedelta

from ..models import ConfigurationEntry, ArchiveLinkDataModel, LinkTagsDataModel
from ..controllers import SourceDataController, LinkDataController, DomainsController
from ..configuration import Configuration
from ..dateutils import DateUtils

from .fakeinternet import FakeInternetTestCase


class LinkDataControllerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def clear(self):
        SourceDataController.objects.all().delete()
        LinkDataController.objects.all().delete()
        ArchiveLinkDataModel.objects.all().delete()

    def create_entries(self, days_before):
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
            date_published=days_before,
        )

        ob = LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=nonbookmarked",
            title="The second link",
            source_obj=source_youtube,
            bookmarked=False,
            language="en",
            domain_obj=domain,
            date_published=days_before,
        )

        ob = LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=permanent",
            title="The first link",
            source_obj=source_youtube,
            permanent=True,
            language="en",
            domain_obj=domain,
            date_published=days_before,
        )

    def test_move_old_links_to_archive(self):
        conf = Configuration.get_object().config_entry

        current_time = DateUtils.get_datetime_now_utc()
        days_before = current_time - timedelta(days=conf.days_to_move_to_archive + 1)

        self.clear()
        self.create_entries(days_before)

        original_date_published = LinkDataController.objects.filter(
            link="https://youtube.com?v=nonbookmarked"
        )[0].date_published

        # call tested function
        LinkDataController.move_old_links_to_archive()

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

        archived = ArchiveLinkDataModel.objects.all()
        domains = DomainsController.objects.all()

        self.assertEqual(archived.count(), 1)
        self.assertEqual(domains.count(), 1)

        self.assertEqual(archived[0].domain_obj, domains[0])
        self.assertEqual(archived[0].date_published, original_date_published)

    def test_clear_old_entries(self):
        conf = Configuration.get_object().config_entry

        current_time = DateUtils.get_datetime_now_utc()
        days_before = current_time - timedelta(days=conf.days_to_remove_links + 2)

        self.clear()
        self.create_entries(days_before)

        # call tested function
        LinkDataController.clear_old_entries()

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
        self.assertEqual(ArchiveLinkDataModel.objects.all().count(), 0)

    def test_get_favicon_empty_in_model(self):
        conf = Configuration.get_object().config_entry

        current_time = DateUtils.get_datetime_now_utc()
        days_before = current_time - timedelta(days=conf.days_to_remove_links + 2)

        self.clear()
        self.create_entries(days_before)

        entries = LinkDataController.objects.filter(thumbnail__isnull=True)

        self.assertTrue(len(entries) != 0)
        self.assertTrue(entries[0].get_favicon() == "https://youtube.com/favicon.ico")

    def test_get_thumbnail_empty_in_model(self):
        conf = Configuration.get_object().config_entry

        current_time = DateUtils.get_datetime_now_utc()
        days_before = current_time - timedelta(days=conf.days_to_remove_links + 2)

        self.clear()
        self.create_entries(days_before)

        entries = LinkDataController.objects.filter(thumbnail__isnull=True)

        self.assertTrue(len(entries) != 0)
        self.assertEqual(entries[0].get_thumbnail(), "https://youtube.com/favicon.ico")

    def test_tag(self):
        current_time = DateUtils.get_datetime_now_utc()
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
            date_published=current_time,
        )

        ob.tag(["test", "tag"], "testuser1")

        tags = LinkTagsDataModel.objects.all()

        self.assertEqual(tags.count(), 2)
