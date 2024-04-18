from datetime import timedelta

from ..controllers import (
    SourceDataController,
    LinkDataController,
    EntryUpdater,
)
from ..configuration import Configuration
from ..dateutils import DateUtils

from .fakeinternet import FakeInternetTestCase


class EntryUpdaterTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_reset_data__fills_properties(self):
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

        u = EntryUpdater(entry)
        # call tested function
        u.reset_data()

        self.assertEqual(entry.title, "LinkedIn Page title")
        self.assertEqual(entry.description, "LinkedIn Page description")
        self.assertEqual(entry.date_published, add_time)
        # self.assertEqual(entry.date_update_last, date_updated)

    def test_update_data__fills_properties(self):
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

        u = EntryUpdater(entry)
        # call tested function
        u.update_data()

        self.assertEqual(entry.title, "LinkedIn Page title")
        self.assertEqual(entry.description, "LinkedIn Page description")
        self.assertEqual(entry.date_published, add_time)
        # self.assertEqual(entry.date_update_last, date_updated)

    def test_update_data__not_reset_properties(self):
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

        u = EntryUpdater(entry)
        # call tested function
        u.update_data()

        self.assertEqual(entry.title, "my title")
        self.assertEqual(entry.description, "my description")
        self.assertEqual(entry.date_published, add_time)
        # self.assertEqual(entry.date_update_last, date_updated)

    def test_reset_data_removes_old_dead_entry(self):
        conf = Configuration.get_object().config_entry

        add_time = DateUtils.get_datetime_now_utc() - timedelta(
            days=conf.days_to_remove_stale_entries + 1
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
            source="",
            link="https://page-with-http-status-500.com",
            title=None,
            description=None,
            source_obj=source_youtube,
            bookmarked=False,
            language=None,
            domain_obj=None,
            date_published=add_time,
            date_dead_since=add_time,
        )

        date_updated = entry.date_update_last

        u = EntryUpdater(entry)
        # call tested function
        u.reset_data()

        entries = LinkDataController.objects.filter(
            link="https://page-with-http-status-500.com"
        )
        self.assertEqual(entries.count(), 0)

    def test_update_data_removes_old_dead_entry(self):
        conf = Configuration.get_object().config_entry

        add_time = DateUtils.get_datetime_now_utc() - timedelta(
            days=conf.days_to_remove_stale_entries + 1
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
            source="",
            link="https://page-with-http-status-500.com",
            title=None,
            description=None,
            source_obj=source_youtube,
            bookmarked=False,
            language=None,
            domain_obj=None,
            thumbnail=None,
            date_published=add_time,
            date_dead_since=add_time,
        )

        date_updated = entry.date_update_last

        u = EntryUpdater(entry)
        # call tested function
        u.update_data()

        entries = LinkDataController.objects.filter(
            link="https://page-with-http-status-500.com"
        )
        self.assertEqual(entries.count(), 0)

    def test_update_data__sets_stale_entry_status(self):
        conf = Configuration.get_object().config_entry

        add_time = DateUtils.get_datetime_now_utc() - timedelta(
            days=conf.days_to_remove_stale_entries - 2
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
            source="",
            link="https://page-with-http-status-500.com",
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

        u = EntryUpdater(entry)
        # call tested function
        u.update_data()

        entries = LinkDataController.objects.filter(
            link="https://page-with-http-status-500.com"
        )
        self.assertEqual(entries.count(), 1)
        self.assertTrue(entries[0].date_dead_since is not None)
        self.assertEqual(entries[0].status_code, 500)
        self.assertEqual(entries[0].manual_status_code, 0)

    def test_update_data__clears_stale_entry_status(self):
        conf = Configuration.get_object().config_entry

        add_time = DateUtils.get_datetime_now_utc() - timedelta(
            days=conf.days_to_remove_stale_entries - 2
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
            source="",
            link="https://youtube.com",
            title=None,
            description=None,
            source_obj=source_youtube,
            bookmarked=False,
            language=None,
            domain_obj=None,
            thumbnail=None,
            date_published=add_time,
            date_dead_since=add_time,
        )

        date_updated = entry.date_update_last

        u = EntryUpdater(entry)
        # call tested function
        u.update_data()

        entries = LinkDataController.objects.filter(link="https://youtube.com")
        self.assertTrue(entries.count(), 1)
        self.assertTrue(entries[0].date_dead_since is None)
        self.assertEqual(entries[0].status_code, 200)
        self.assertEqual(entries[0].manual_status_code, 0)
