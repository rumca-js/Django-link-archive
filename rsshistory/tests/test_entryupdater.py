from datetime import timedelta
from django.contrib.auth.models import User

from utils.dateutils import DateUtils

from ..controllers import (
    SourceDataController,
    LinkDataController,
    EntryUpdater,
    BackgroundJobController,
)
from ..models import UserTags, UserVotes
from ..configuration import Configuration

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class EntryUpdaterTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()
        self.setup_configuration()

        conf = Configuration.get_object().config_entry
        conf.keep_domains = False
        conf.save()

        self.user = User.objects.create_user(
            username="TestUser", password="testpassword", is_staff=True
        )

    def test_update_data__fills_properties(self):
        add_time = DateUtils.get_datetime_now_utc() - timedelta(days=1)

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            export_to_cms=True,
            remove_after_days=1,
        )

        entry = LinkDataController.objects.create(
            source_url="",
            link="https://linkedin.com",
            title=None,
            description=None,
            source=source_youtube,
            bookmarked=False,
            language=None,
            domain=None,
            thumbnail=None,
            date_published=add_time,
        )

        date_updated = entry.date_update_last

        u = EntryUpdater(entry)
        # call tested function
        u.update_data()

        self.assertEqual(entry.title, "Https LinkedIn Page title")
        self.assertEqual(entry.description, "LinkedIn Page description")
        self.assertEqual(entry.date_published, add_time)
        # self.assertEqual(entry.date_update_last, date_updated)
        
    def test_update_data__adds_scan_job(self):
        add_time = DateUtils.get_datetime_now_utc() - timedelta(days=1)

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            export_to_cms=True,
            remove_after_days=1,
        )

        entry = LinkDataController.objects.create(
            source_url="",
            link="https://linkedin.com",
            title=None,
            description=None,
            source=source_youtube,
            bookmarked=False,
            language=None,
            domain=None,
            thumbnail=None,
            date_published=add_time,
        )

        date_updated = entry.date_update_last

        u = EntryUpdater(entry)
        # call tested function
        u.update_data()

        scan_jobs = BackgroundJobController.objects.filter(job = BackgroundJobController.JOB_LINK_SCAN)
        self.assertEqual(scan_jobs.count(), 1)

    def test_update_data__not_reset_properties(self):
        MockRequestCounter.mock_page_requests = 0

        add_time = DateUtils.get_datetime_now_utc() - timedelta(days=1)

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            export_to_cms=True,
            remove_after_days=1,
        )

        entry = LinkDataController.objects.create(
            source_url="",
            link="https://linkedin.com",
            title="my title",
            description="my description",
            bookmarked=False,
            language="pl",
            domain=None,
            date_published=add_time,
            thumbnail="thumbnail",
            source=source_youtube,
        )

        date_updated = entry.date_update_last

        u = EntryUpdater(entry)
        # call tested function
        u.update_data()

        self.assertEqual(entry.title, "my title")
        self.assertEqual(entry.description, "my description")
        self.assertEqual(entry.date_published, add_time)
        # self.assertEqual(entry.date_update_last, date_updated)

        self.assertEqual(MockRequestCounter.mock_page_requests, 2)

    def test_update_data__removes_old_dead_entry(self):
        MockRequestCounter.mock_page_requests = 0
        conf = Configuration.get_object().config_entry

        add_time = DateUtils.get_datetime_now_utc() - timedelta(
            days=conf.days_to_remove_stale_entries + 1
        )

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            export_to_cms=True,
            remove_after_days=1,
        )

        entry = LinkDataController.objects.create(
            source_url="",
            link="https://page-with-http-status-500.com",
            title=None,
            description=None,
            source=source_youtube,
            bookmarked=False,
            language=None,
            domain=None,
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
        self.assertEqual(MockRequestCounter.mock_page_requests, 6)

    def test_update_data__sets_stale_entry_status(self):
        MockRequestCounter.mock_page_requests = 0
        conf = Configuration.get_object().config_entry

        add_time = DateUtils.get_datetime_now_utc() - timedelta(
            days=conf.days_to_remove_stale_entries - 2
        )

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            export_to_cms=True,
            remove_after_days=1,
        )

        entry = LinkDataController.objects.create(
            source_url="",
            link="https://page-with-http-status-500.com",
            title=None,
            description=None,
            source=source_youtube,
            bookmarked=False,
            language=None,
            domain=None,
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

        self.assertEqual(MockRequestCounter.mock_page_requests, 6)

    def test_update_data__clears_stale_entry_status(self):
        MockRequestCounter.mock_page_requests = 0

        conf = Configuration.get_object().config_entry

        add_time = DateUtils.get_datetime_now_utc() - timedelta(
            days=conf.days_to_remove_stale_entries - 2
        )

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            export_to_cms=True,
            remove_after_days=1,
        )

        entry = LinkDataController.objects.create(
            source_url="",
            link="https://youtube.com",
            title=None,
            description=None,
            source=source_youtube,
            bookmarked=False,
            language=None,
            domain=None,
            thumbnail=None,
            date_published=add_time,
            date_dead_since=add_time,
        )

        date_updated = entry.date_update_last

        u = EntryUpdater(entry)
        # call tested function
        u.update_data()

        entries = LinkDataController.objects.filter(link="https://youtube.com")
        self.assertEqual(entries.count(), 1)
        self.assertTrue(entries[0].date_dead_since is None)
        self.assertEqual(entries[0].status_code, 200)
        self.assertEqual(entries[0].manual_status_code, 0)

        self.assertEqual(MockRequestCounter.mock_page_requests, 2)

    def test_update_data__no_properties_does_not_delete(self):
        MockRequestCounter.mock_page_requests = 0

        conf = Configuration.get_object().config_entry

        add_time = DateUtils.get_datetime_now_utc() - timedelta(
            days=conf.days_to_remove_stale_entries - 2
        )

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            export_to_cms=True,
            remove_after_days=1,
        )

        entry = LinkDataController.objects.create(
            source_url="",
            link="https://no-props-page.com",
            title="some title",
            description="some description",
            source=source_youtube,
            bookmarked=False,
            language=None,
            domain=None,
            thumbnail=None,
            date_published=add_time,
            date_dead_since=add_time,
        )

        date_updated = entry.date_update_last

        u = EntryUpdater(entry)
        # call tested function
        u.update_data()

        entries = LinkDataController.objects.filter(link="https://no-props-page.com")
        self.assertEqual(entries.count(), 1)
        self.assertTrue(entries[0].date_dead_since is None)
        self.assertEqual(entries[0].status_code, 200)
        self.assertEqual(entries[0].title, "some title")
        self.assertEqual(entries[0].description, "some description")
        self.assertEqual(entries[0].manual_status_code, 0)

        self.assertEqual(MockRequestCounter.mock_page_requests, 2)

    def test_update_data__updates_thumbnail(self):
        MockRequestCounter.mock_page_requests = 0

        conf = Configuration.get_object().config_entry

        add_time = DateUtils.get_datetime_now_utc() - timedelta(
            days=conf.days_to_remove_stale_entries - 2
        )

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            export_to_cms=True,
            remove_after_days=1,
        )

        entry = LinkDataController.objects.create(
            source_url="",
            link="https://youtube.com/watch?v=1234",
            title="some title",
            description="some description",
            source=source_youtube,
            bookmarked=False,
            language=None,
            domain=None,
            thumbnail="https://some-old-thumbnail.com/thumbnail.jpg",
            date_published=add_time,
            date_dead_since=add_time,
        )

        date_updated = entry.date_update_last

        u = EntryUpdater(entry)
        # call tested function
        u.update_data()

        entries = LinkDataController.objects.filter(link="https://youtube.com/watch?v=1234")
        self.assertEqual(entries.count(), 1)
        self.assertTrue(entries[0].thumbnail, "https://youtube.com/files/1234-thumbnail.png")

    def test_update_data__removes_casinos(self):
        MockRequestCounter.mock_page_requests = 0

        add_time = DateUtils.get_datetime_now_utc() - timedelta(days=1)

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            export_to_cms=True,
            remove_after_days=1,
        )

        entry = LinkDataController.objects.create(
            source_url="",
            link="https://slot-casino-page.com",
            title="Casino casino casino casino casino",
            description=None,
            source=source_youtube,
            bookmarked=False,
            language=None,
            domain=None,
            thumbnail=None,
            date_published=add_time,
        )

        date_updated = entry.date_update_last

        u = EntryUpdater(entry)
        # call tested function
        u.update_data()

        self.assertEqual(LinkDataController.objects.all().count(), 0)

        self.assertEqual(MockRequestCounter.mock_page_requests, 2)

    def test_reset_data__fills_properties(self):
        add_time = DateUtils.get_datetime_now_utc() - timedelta(days=1)

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            export_to_cms=True,
            remove_after_days=1,
        )

        entry = LinkDataController.objects.create(
            source_url="",
            link="https://linkedin.com",
            title=None,
            description=None,
            source=source_youtube,
            bookmarked=False,
            language=None,
            domain=None,
            date_published=add_time,
        )

        date_updated = entry.date_update_last

        u = EntryUpdater(entry)
        # call tested function
        u.reset_data()

        self.assertEqual(entry.title, "Https LinkedIn Page title")
        self.assertEqual(entry.description, "LinkedIn Page description")
        self.assertEqual(entry.date_published, add_time)
        # self.assertEqual(entry.date_update_last, date_updated)
        
    def test_reset_data__adds_scan_job(self):
        add_time = DateUtils.get_datetime_now_utc() - timedelta(days=1)

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            export_to_cms=True,
            remove_after_days=1,
        )

        entry = LinkDataController.objects.create(
            source_url="",
            link="https://linkedin.com",
            title=None,
            description=None,
            source=source_youtube,
            bookmarked=False,
            language=None,
            domain=None,
            date_published=add_time,
        )

        date_updated = entry.date_update_last

        u = EntryUpdater(entry)
        # call tested function
        u.reset_data()

        scan_jobs = BackgroundJobController.objects.filter(job = BackgroundJobController.JOB_LINK_SCAN)
        self.assertEqual(scan_jobs.count(), 1)

    def test_reset_data__removes_old_dead_entry(self):
        MockRequestCounter.mock_page_requests = 0

        conf = Configuration.get_object().config_entry

        add_time = DateUtils.get_datetime_now_utc() - timedelta(
            days=conf.days_to_remove_stale_entries + 1
        )

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            export_to_cms=True,
            remove_after_days=1,
        )

        entry = LinkDataController.objects.create(
            source_url="",
            link="https://page-with-http-status-500.com",
            title=None,
            description=None,
            source=source_youtube,
            bookmarked=False,
            language=None,
            domain=None,
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
        self.assertEqual(MockRequestCounter.mock_page_requests, 6)

    def test_reset_local_data(self):
        MockRequestCounter.mock_page_requests = 0

        conf = Configuration.get_object().config_entry

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            export_to_cms=True,
            remove_after_days=1,
        )

        entry = LinkDataController.objects.create(
            source_url="",
            link="https://youtube.com",
            title=None,
            description=None,
            source=source_youtube,
            bookmarked=True,
            language=None,
            domain=None,
            thumbnail=None,
        )

        entry.page_rating_contents = 100

        UserTags.set_tag(entry, "test", user=self.user)
        UserVotes.add(self.user, entry, 100)

        u = EntryUpdater(entry)
        # call tested function
        u.reset_local_data()

        entries = LinkDataController.objects.filter(link="https://youtube.com")
        self.assertEqual(entries.count(), 1)
        self.assertEqual(entries[0].page_rating_votes, 100)
        self.assertEqual(entries[0].page_rating_contents, 100)
        self.assertEqual(entries[0].page_rating, 100)

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_reset_data__no_properties_does_not_delete(self):
        MockRequestCounter.mock_page_requests = 0

        conf = Configuration.get_object().config_entry

        add_time = DateUtils.get_datetime_now_utc() - timedelta(
            days=conf.days_to_remove_stale_entries - 2
        )

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            export_to_cms=True,
            remove_after_days=1,
        )

        entry = LinkDataController.objects.create(
            source_url="",
            link="https://no-props-page.com",
            title="some title",
            description="some description",
            source=source_youtube,
            bookmarked=False,
            language=None,
            domain=None,
            thumbnail=None,
            date_published=add_time,
            date_dead_since=add_time,
        )

        date_updated = entry.date_update_last

        u = EntryUpdater(entry)
        # call tested function
        u.reset_data()

        entries = LinkDataController.objects.filter(link="https://no-props-page.com")
        self.assertEqual(entries.count(), 1)
        self.assertTrue(entries[0].date_dead_since is None)
        self.assertEqual(entries[0].status_code, 200)
        self.assertEqual(entries[0].title, "some title")
        self.assertEqual(entries[0].description, "some description")
        self.assertEqual(entries[0].manual_status_code, 0)

        self.assertEqual(MockRequestCounter.mock_page_requests, 2)
