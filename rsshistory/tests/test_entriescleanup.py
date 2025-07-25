from datetime import timedelta
from django.contrib.auth.models import User

from utils.dateutils import DateUtils

from ..models import UserBookmarks, EntryRules
from ..controllers import (
    EntryWrapper,
    SourceDataController,
    DomainsController,
    EntriesCleanup,
)
from ..controllers import LinkDataController, ArchiveLinkDataController
from ..configuration import Configuration

from .fakeinternet import FakeInternetTestCase


class EntriesCleanupTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            export_to_cms=True,
        )

        self.user_staff = User.objects.create_user(
            username="TestUser", password="testpassword", is_staff=True
        )
        self.user_not_staff = User.objects.create_user(
            username="TestUserNot", password="testpassword", is_staff=False
        )

        conf = Configuration.get_object().config_entry
        conf.auto_scan_new_entries = True
        conf.save()

    def clear(self):
        SourceDataController.objects.all().delete()
        LinkDataController.objects.all().delete()
        ArchiveLinkDataController.objects.all().delete()

    def create_entries(self, date_link_publish, date_to_remove):
        self.domain = DomainsController.objects.create(
            domain="https://youtube.com",
        )

        self.source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            export_to_cms=True,
            remove_after_days=1,
        )

        ob = LinkDataController.objects.create(
            source_url="https://youtube.com",
            source=self.source_youtube,
            link="https://youtube.com?v=bookmarked",
            title="The first link",
            bookmarked=True,
            language="en",
            domain=self.domain,
            date_published=date_link_publish,
        )
        UserBookmarks.add(self.user_not_staff, ob)

        ob = LinkDataController.objects.create(
            source_url="https://youtube.com",
            source=self.source_youtube,
            link="https://youtube.com?v=nonbookmarked",
            title="The second link",
            bookmarked=False,
            language="en",
            domain=self.domain,
            date_published=date_link_publish,
        )

        ob = LinkDataController.objects.create(
            source_url="https://youtube.com",
            source=self.source_youtube,
            link="https://youtube.com",
            title="The first link",
            permanent=True,
            language="en",
            domain=self.domain,
            date_published=date_link_publish,
        )

        ob = ArchiveLinkDataController.objects.create(
            source_url="https://youtube.com",
            source=self.source_youtube,
            link="https://youtube.com?v=nonbookmarked2",
            title="The second link",
            bookmarked=False,
            language="en",
            domain=self.domain,
            date_published=date_to_remove,
        )

    def test_cleanup__remove_old(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_remove_links = 2
        # conf.days_to_move_to_archive = 1
        conf.accept_domain_links = True
        conf.save()

        current_time = DateUtils.get_datetime_now_utc()
        date_link_publish = current_time - timedelta(days=conf.days_to_remove_links + 2)
        date_to_remove = current_time - timedelta(days=conf.days_to_remove_links + 2)

        self.clear()
        self.create_entries(date_link_publish, date_to_remove)

        nonbookmarked = LinkDataController.objects.filter(
            link="https://youtube.com?v=nonbookmarked"
        )
        self.assertEqual(nonbookmarked.count(), 1)
        self.assertEqual(nonbookmarked[0].bookmarked, False)

        # call tested function
        EntriesCleanup().cleanup()

        nonbookmarked = LinkDataController.objects.filter(
            link="https://youtube.com?v=nonbookmarked"
        )
        self.assertEqual(nonbookmarked.count(), 0)

    def test_cleanup__not_remove_bookmarked(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_remove_links = 2
        # conf.days_to_move_to_archive = 1
        conf.accept_domain_links = True
        conf.save()

        current_time = DateUtils.get_datetime_now_utc()
        date_link_publish = current_time - timedelta(days=conf.days_to_remove_links + 2)
        date_to_remove = current_time - timedelta(days=conf.days_to_remove_links + 2)

        self.clear()
        self.create_entries(date_link_publish, date_to_remove)

        bookmarked = LinkDataController.objects.filter(
            link="https://youtube.com?v=bookmarked"
        )
        self.assertEqual(bookmarked.count(), 1)
        self.assertEqual(bookmarked[0].bookmarked, True)

        # call tested function
        EntriesCleanup().cleanup()

        bookmarked = LinkDataController.objects.filter(
            link="https://youtube.com?v=bookmarked"
        )
        self.assertEqual(bookmarked.count(), 1)

    def test_cleanup__not_remove_permanent(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_remove_links = 2
        # conf.days_to_move_to_archive = 1
        conf.accept_domain_links = True
        conf.save()

        current_time = DateUtils.get_datetime_now_utc()
        date_link_publish = current_time - timedelta(days=conf.days_to_remove_links + 2)
        date_to_remove = current_time - timedelta(days=conf.days_to_remove_links + 2)

        self.clear()
        self.create_entries(date_link_publish, date_to_remove)

        permanent = LinkDataController.objects.filter(link="https://youtube.com")
        self.assertEqual(permanent.count(), 1)
        self.assertEqual(permanent[0].permanent, True)

        # call tested function
        EntriesCleanup().cleanup()

        permanent = LinkDataController.objects.filter(link="https://youtube.com")
        self.assertEqual(permanent.count(), 1)

    def test_cleanup__removes_old_entries_archive(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_remove_links = 2
        conf.save()

        current_time = DateUtils.get_datetime_now_utc()
        date_link_publish = current_time - timedelta(days=conf.days_to_remove_links + 2)
        date_to_remove = current_time - timedelta(days=conf.days_to_remove_links + 2)

        self.clear()

        ob = ArchiveLinkDataController.objects.create(
            source_url="https://youtube.com",
            source=self.source_youtube,
            link="https://youtube.com?v=nonbookmarked2",
            title="The second link",
            bookmarked=False,
            language="en",
            date_published=date_to_remove,
        )

        # call tested function
        EntriesCleanup(archive_cleanup=True).cleanup()

        self.assertEqual(ArchiveLinkDataController.objects.all().count(), 0)

    def test_cleanup__entry_rules(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_remove_links = 2
        # conf.days_to_move_to_archive = 1
        conf.accept_domain_links = True
        conf.save()

        EntryRules.objects.create(block=True, trigger_rule_url="youtube.com")

        bookmarked = LinkDataController.objects.create(
            link="https://youtube.com?v=bookmarked"
        )

        # call tested function
        EntriesCleanup().cleanup()

        bookmarked = LinkDataController.objects.filter(
            link="https://youtube.com?v=bookmarked"
        )

        EntryRules.objects.all().delete()

    def test_get_stale_entries__not_dead(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_remove_links = 2
        conf.days_to_remove_stale_entries = 4
        conf.accept_domain_links = True
        conf.save()

        days_before_remove = DateUtils.get_days_before_dt(conf.days_to_remove_links)
        days_before_stale = DateUtils.get_days_before_dt(
            conf.days_to_remove_stale_entries
        )

        not_dead = LinkDataController.objects.create(
            link="https://youtube.com?v=1",
        )

        # call tested function
        entries = EntriesCleanup().get_stale_entries()

        self.assertEqual(entries.count(), 0)

    def test_get_stale_entries__dead_not_stale(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_remove_links = 2
        conf.days_to_remove_stale_entries = 4
        conf.accept_domain_links = True
        conf.save()

        days_before_remove = DateUtils.get_days_before_dt(conf.days_to_remove_links)
        days_before_stale = DateUtils.get_days_before_dt(
            conf.days_to_remove_stale_entries
        )

        dead_not_stale = LinkDataController.objects.create(
            link="https://youtube.com?v=2",
            date_dead_since=days_before_remove - timedelta(days=1),
            date_created=days_before_remove - timedelta(days=1),
        )

        # call tested function
        entries = EntriesCleanup().get_stale_entries()

        self.assertEqual(entries.count(), 0)

    def test_get_stale_entries__dead_and_stale(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_remove_links = 2
        conf.days_to_remove_stale_entries = 4
        conf.accept_domain_links = True
        conf.save()

        days_before_remove = DateUtils.get_days_before_dt(conf.days_to_remove_links)
        days_before_stale = DateUtils.get_days_before_dt(
            conf.days_to_remove_stale_entries
        )

        dead_and_stale = LinkDataController.objects.create(
            link="https://youtube.com?v=3",
            date_dead_since=days_before_stale - timedelta(days=1),
            date_created=days_before_stale - timedelta(days=1),
            status_code=500,
        )

        # call tested function
        entries = EntriesCleanup().get_stale_entries()

        self.assertEqual(entries.count(), 1)

    def test_get_stale_entries__dead_stale_but_status_code_ok(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_remove_links = 2
        conf.days_to_remove_stale_entries = 4
        conf.accept_domain_links = True
        conf.save()

        days_before_remove = DateUtils.get_days_before_dt(conf.days_to_remove_links)
        days_before_stale = DateUtils.get_days_before_dt(
            conf.days_to_remove_stale_entries
        )

        dead_stale_but_ok = LinkDataController.objects.create(
            link="https://youtube.com?v=4",
            date_dead_since=days_before_stale - timedelta(days=1),
            date_created=days_before_stale - timedelta(days=1),
            status_code=200,
        )

        # call tested function
        entries = EntriesCleanup().get_stale_entries()

        self.assertEqual(entries.count(), 0)

    def test_get_stale_entries__dead_stale_but_status_code_unknown(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_remove_links = 2
        conf.days_to_remove_stale_entries = 4
        conf.accept_domain_links = True
        conf.save()

        days_before_remove = DateUtils.get_days_before_dt(conf.days_to_remove_links)
        days_before_stale = DateUtils.get_days_before_dt(
            conf.days_to_remove_stale_entries
        )

        dead_stale_but_ok = LinkDataController.objects.create(
            link="https://youtube.com?v=4",
            date_dead_since=days_before_stale - timedelta(days=1),
            date_created=days_before_stale - timedelta(days=1),
            status_code=0,
        )

        # call tested function
        entries = EntriesCleanup().get_stale_entries()

        self.assertEqual(entries.count(), 0)

    def test_get_stale_entries__dead_stale_but_votes(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_remove_links = 2
        conf.days_to_remove_stale_entries = 4
        conf.accept_domain_links = True
        conf.save()

        days_before_remove = DateUtils.get_days_before_dt(conf.days_to_remove_links)
        days_before_stale = DateUtils.get_days_before_dt(
            conf.days_to_remove_stale_entries
        )

        dead_stale_but_ok = LinkDataController.objects.create(
            link="https://youtube.com?v=4",
            date_dead_since=days_before_stale - timedelta(days=1),
            date_created=days_before_stale - timedelta(days=1),
            page_rating_votes=1,
        )

        # call tested function
        entries = EntriesCleanup().get_stale_entries()

        self.assertEqual(entries.count(), 0)

    def test_get_stale_entries__dead_stale_but_manual_status_ok(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_remove_links = 2
        conf.days_to_remove_stale_entries = 4
        conf.accept_domain_links = True
        conf.save()

        days_before_remove = DateUtils.get_days_before_dt(conf.days_to_remove_links)
        days_before_stale = DateUtils.get_days_before_dt(
            conf.days_to_remove_stale_entries
        )

        dead_stale_but_ok = LinkDataController.objects.create(
            link="https://youtube.com?v=4",
            date_dead_since=days_before_stale - timedelta(days=1),
            date_created=days_before_stale - timedelta(days=1),
            status_code=500,
            manual_status_code=200,
        )

        # call tested function
        entries = EntriesCleanup().get_stale_entries()

        self.assertEqual(entries.count(), 0)

    def test_get_stale_entries__dead_but_bookmarked(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_remove_links = 2
        conf.days_to_remove_stale_entries = 4
        conf.accept_domain_links = True
        conf.save()

        days_before_remove = DateUtils.get_days_before_dt(conf.days_to_remove_links)
        days_before_stale = DateUtils.get_days_before_dt(
            conf.days_to_remove_stale_entries
        )

        dead_stale_but_bookmarked = LinkDataController.objects.create(
            link="https://youtube.com?v=5",
            date_dead_since=days_before_stale - timedelta(days=1),
            date_created=days_before_stale - timedelta(days=1),
            bookmarked=True,
        )

        # call tested function
        entries = EntriesCleanup().get_stale_entries()

        self.assertEqual(entries.count(), 0)

    def test_get_stale_entries__dead_but_permanent(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_remove_links = 2
        conf.days_to_remove_stale_entries = 4
        conf.accept_domain_links = True
        conf.save()

        days_before_remove = DateUtils.get_days_before_dt(conf.days_to_remove_links)
        days_before_stale = DateUtils.get_days_before_dt(
            conf.days_to_remove_stale_entries
        )

        dead_stale_but_permanent = LinkDataController.objects.create(
            link="https://youtube.com?v=6",
            date_dead_since=days_before_stale - timedelta(days=1),
            date_created=days_before_stale - timedelta(days=1),
            bookmarked=True,
        )

        # call tested function
        entries = EntriesCleanup().get_stale_entries()

        self.assertEqual(entries.count(), 0)

    def test_move_old_links_to_archive(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_move_to_archive = 1
        conf.days_to_remove_links = 2
        conf.save()

        current_time = DateUtils.get_datetime_now_utc()
        date_link_publish = current_time - timedelta(
            days=conf.days_to_move_to_archive + 1
        )
        date_to_remove = current_time - timedelta(days=conf.days_to_remove_links + 1)

        self.clear()
        self.create_entries(date_link_publish, date_to_remove)

        original_date_published = LinkDataController.objects.filter(
            link="https://youtube.com?v=nonbookmarked"
        )[0].date_published

        # call tested function
        EntriesCleanup(archive_cleanup=True).move_old_links_to_archive()

        nonbookmarked = LinkDataController.objects.filter(
            link="https://youtube.com?v=nonbookmarked"
        )
        self.assertEqual(nonbookmarked.count(), 0)

        archived = ArchiveLinkDataController.objects.all()
        domains = DomainsController.objects.all()

        self.assertEqual(archived.count(), 2)
        self.assertEqual(domains.count(), 1)

        self.assertEqual(archived[0].domain, domains[0])
        self.assertEqual(archived[0].date_published, date_link_publish)

        self.assertEqual(archived[1].domain, domains[0])
        self.assertEqual(archived[1].date_published, date_to_remove)
