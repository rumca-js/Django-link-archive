from datetime import timedelta

from ..models import LinkTagsDataModel
from ..controllers import (
    SourceDataController,
    LinkDataController,
    ArchiveLinkDataController,
    DomainsController,
)
from ..configuration import Configuration
from ..dateutils import DateUtils

from .fakeinternet import FakeInternetTestCase


class LinkDataControllerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

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

        entry = LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=bookmarked",
            title="The first link",
            source_obj=source_youtube,
            bookmarked=True,
            language="en",
            domain_obj=domain,
            date_published=current_time,
        )

        # call tested function
        entry.tag(["tag1", "tag2"], "testuser1")

        tags = LinkTagsDataModel.objects.all()

        self.assertEqual(tags.count(), 2)
        self.assertEqual(tags[0].tag, "tag2")
        self.assertEqual(tags[1].tag, "tag1")

    def test_reset_data_none(self):
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
            title=None,
            description=None,
            source_obj=source_youtube,
            bookmarked=False,
            language=None,
            domain_obj=None,
            date_published=add_time,
        )

        date_updated = entry.date_update_last

        # call tested function
        entry.reset_data()

        self.assertEqual(entry.title, "LinkedIn Page title")
        self.assertEqual(entry.description, "LinkedIn Page description")
        self.assertEqual(entry.date_published, add_time)
        # self.assertEqual(entry.date_update_last, date_updated)

    def test_update_data_none(self):
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
            title=None,
            description=None,
            source_obj=source_youtube,
            bookmarked=False,
            language=None,
            domain_obj=None,
            thumbnail=None,
            date_published=add_time,
        )

        date_updated = entry.date_update_last

        # call tested function
        entry.update_data()

        self.assertEqual(entry.title, "LinkedIn Page title")
        self.assertEqual(entry.description, "LinkedIn Page description")
        self.assertEqual(entry.date_published, add_time)
        # self.assertEqual(entry.date_update_last, date_updated)

    def test_update_data_not_none(self):
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
        entry.update_data()

        self.assertEqual(entry.title, "my title")
        self.assertEqual(entry.description, "my description")
        self.assertEqual(entry.date_published, add_time)
        # self.assertEqual(entry.date_update_last, date_updated)
