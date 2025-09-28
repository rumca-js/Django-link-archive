from datetime import timedelta
from django.contrib.auth.models import User

from utils.dateutils import DateUtils

from ..controllers import (
    EntryDataBuilder,
    EntryWrapper,
    SourceDataController,
    DomainsController,
    BackgroundJobController,
    LinkDataController,
    ArchiveLinkDataController,
    common_initialize_entry_rules,
)
from ..models import LinkDataModel, EntryRules
from ..configuration import Configuration

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class EntryDataBuilderTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()
        self.setup_configuration()

        LinkDataController.objects.all().delete()
        ArchiveLinkDataController.objects.all().delete()

        self.user = User.objects.create_user(
            username="TestUser", password="testpassword", is_staff=True
        )

    def test_build_from_props__no_slash(self):
        config = Configuration.get_object().config_entry
        config.accept_non_domain_links = True
        config.accept_domain_links = False
        config.auto_create_sources = False
        config.auto_scan_new_entries = True
        config.save()

        EntryRules.objects.all().delete()

        MockRequestCounter.mock_page_requests = 0

        link_name = "https://youtube.com/v=1234"

        current_time = DateUtils.get_datetime_now_utc()
        creation_date = current_time - timedelta(days=1)

        link_data = {
            "link": link_name,
            "source_url": "https://youtube.com",
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": creation_date,
            "page_rating_contents": 23,
            "page_rating_votes": 12,
            "page_rating": 25,
        }

        b = EntryDataBuilder()
        b.user = self.user
        b.link_data = link_data
        # call tested function
        entry = b.build_from_props()

        objs = LinkDataController.objects.filter(link=link_name)

        self.assertEqual(objs.count(), 1)
        self.assertEqual(objs[0].link, link_name)
        self.assertEqual(objs[0].date_published, creation_date)
        self.assertEqual(objs[0].user, self.user)

        self.assertEqual(objs[0].page_rating_contents, 23)
        # votes are reset
        self.assertEqual(objs[0].page_rating_votes, 0)
        # visits are reset
        self.assertEqual(objs[0].page_rating_visits, 0)
        # rating is recalculated
        self.assertEqual(objs[0].page_rating, 7)

        # this is obtained not through page requests
        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_build_from_props__with_slash(self):
        config = Configuration.get_object().config_entry
        config.accept_non_domain_links = True
        config.accept_domain_links = False
        config.auto_scan_new_entries = True
        config.save()

        EntryRules.objects.all().delete()

        link_name = "https://youtube.com/v=1234/"

        link_data = {
            "link": link_name,
            "source_url": "https://youtube.com",
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": DateUtils.get_datetime_now_utc(),
        }

        b = EntryDataBuilder()
        b.link_data = link_data
        # call tested function
        entry = b.build_from_props()

        objs = LinkDataController.objects.filter(link="https://youtube.com/v=1234/")
        self.assertEqual(objs.count(), 0)

        objs = LinkDataController.objects.filter(link="https://youtube.com/v=1234")
        self.assertEqual(objs.count(), 1)

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_build_from_props__uppercase(self):
        config = Configuration.get_object().config_entry
        config.accept_non_domain_links = True
        config.accept_domain_links = False
        config.auto_scan_new_entries = True
        config.save()

        EntryRules.objects.all().delete()

        link_name = "HTTPS://YouTube.com/v=1234/"

        link_data = {
            "link": link_name,
            "source_url": "https://youtube.com",
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": DateUtils.get_datetime_now_utc(),
        }

        b = EntryDataBuilder()
        b.link_data = link_data
        # call tested function
        entry = b.build_from_props()

        objs = LinkDataController.objects.filter(link="https://youtube.com/v=1234/")
        self.assertEqual(objs.count(), 0)

        objs = LinkDataController.objects.filter(link="https://youtube.com/v=1234")
        self.assertEqual(objs.count(), 1)

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_build_from_props__not_adds(self):
        DomainsController.objects.all().delete()
        LinkDataController.objects.all().delete()

        config = Configuration.get_object().config_entry
        config.accept_non_domain_links = False
        config.accept_domain_links = False
        config.save()

        EntryRules.objects.all().delete()

        objs = LinkDataController.objects.all()
        self.assertEqual(objs.count(), 0)

        link_name_0 = "https://youtube.com/v=1234"

        link_data = {
            "link": link_name_0,
            "source_url": "https://youtube.com",
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": DateUtils.get_datetime_now_utc(),
            "bookmarked": False,
        }

        b = EntryDataBuilder(source_is_auto=True)
        b.link_data = link_data
        # call tested function
        entry = b.build_from_props()

        objs = LinkDataController.objects.all()
        self.assertEqual(objs.count(), 0)

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_build_from_props__adds_domain(self):
        DomainsController.objects.all().delete()
        LinkDataController.objects.all().delete()

        config = Configuration.get_object().config_entry
        config.accept_non_domain_links = False
        config.accept_domain_links = True
        config.auto_scan_new_entries = True
        config.save()

        EntryRules.objects.all().delete()

        MockRequestCounter.mock_page_requests = 0

        link_name_0 = "https://youtube.com/v=1234"

        link_data = {
            "link": link_name_0,
            "source_url": "https://youtube.com",
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": DateUtils.get_datetime_now_utc(),
            "bookmarked": True,
        }

        b = EntryDataBuilder(source_is_auto=True)
        b.link_data = link_data
        # call tested function
        entry = b.build_from_props()

        objs = LinkDataController.objects.all()
        domains = DomainsController.objects.all()

        for domain in domains:
            print("Domain:{}".format(domain.domain))

        # for each domain an entry is created
        self.assertEqual(objs.count(), 0)

        jobs = BackgroundJobController.objects.all()
        self.assertEqual(jobs.count(), 1)
        self.assertEqual(jobs[0].subject, "https://youtube.com")

        link_name_1 = "https://youtube.com/v=1235"

        link_data = {
            "link": link_name_1,
            "source_url": "https://youtube.com",
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": DateUtils.get_datetime_now_utc(),
            "bookmarked": True,
        }

        b = EntryDataBuilder(source_is_auto=True)
        b.link_data = link_data
        # call tested function
        entry = b.build_from_props()

        objs = LinkDataController.objects.all()
        domains = DomainsController.objects.all()

        # for each domain an entry is created
        self.assertEqual(objs.count(), 0)

        jobs = BackgroundJobController.objects.all()
        self.assertEqual(jobs.count(), 1)
        self.assertEqual(jobs[0].subject, "https://youtube.com")

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_build_from_props__site_not_found(self):
        config = Configuration.get_object().config_entry
        config.accept_non_domain_links = True
        config.accept_domain_links = False
        config.auto_create_sources = False
        config.auto_scan_new_entries = True
        config.save()

        EntryRules.objects.all().delete()
        common_initialize_entry_rules()

        MockRequestCounter.mock_page_requests = 0

        link_name = "https://youtube.com/v=1234"

        current_time = DateUtils.get_datetime_now_utc()
        creation_date = current_time - timedelta(days=1)

        link_data = {
            "link": link_name,
            "source_url": "https://youtube.com",
            "title": "Site not found - GitHub",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": creation_date,
            "page_rating_contents": 23,
            "page_rating_votes": 12,
            "page_rating": 25,
        }

        b = EntryDataBuilder()

        # call tested function
        entry = b.build(link_data=link_data, source_is_auto=True)

        objs = LinkDataController.objects.filter(link=link_name)
        self.assertEqual(objs.count(), 0)

    def test_build_from_props__ipv4_rejects(self):
        config = Configuration.get_object().config_entry
        config.accept_non_domain_links = True
        config.accept_domain_links = False
        config.auto_create_sources = False
        config.accept_ip_links = False
        config.auto_scan_new_entries = True
        config.save()

        EntryRules.objects.all().delete()

        MockRequestCounter.mock_page_requests = 0

        link_name = "https://127.0.0.1/v=1234"

        current_time = DateUtils.get_datetime_now_utc()
        creation_date = current_time - timedelta(days=1)

        link_data = {
            "link": link_name,
            "source_url": "https://youtube.com",
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": creation_date,
            "page_rating_contents": 23,
            "page_rating_votes": 12,
            "page_rating": 25,
        }

        b = EntryDataBuilder()
        b.link_data = link_data
        # call tested function
        entry = b.build_from_props()

        objs = LinkDataController.objects.filter(link=link_name)

        self.assertEqual(objs.count(), 0)

    def test_build_from_props__ipv4_accept(self):
        config = Configuration.get_object().config_entry
        config.accept_non_domain_links = True
        config.accept_domain_links = False
        config.auto_create_sources = False
        config.accept_ip_links = True
        config.auto_scan_new_entries = True
        config.save()

        EntryRules.objects.all().delete()

        MockRequestCounter.mock_page_requests = 0

        link_name = "https://127.0.0.1/v=1234"

        current_time = DateUtils.get_datetime_now_utc()
        creation_date = current_time - timedelta(days=1)

        link_data = {
            "link": link_name,
            "source_url": "https://youtube.com",
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": creation_date,
            "page_rating_contents": 23,
            "page_rating_votes": 12,
            "page_rating": 25,
        }

        b = EntryDataBuilder()
        b.link_data = link_data
        # call tested function
        entry = b.build_from_props()

        objs = LinkDataController.objects.filter(link=link_name)

        self.assertEqual(objs.count(), 1)

    def test_build_from_props__adds_date_published(self):
        config = Configuration.get_object().config_entry
        config.accept_non_domain_links = True
        config.accept_domain_links = False
        config.auto_create_sources = False
        config.accept_ip_links = True
        config.auto_scan_new_entries = True
        config.save()

        EntryRules.objects.all().delete()

        MockRequestCounter.mock_page_requests = 0

        link_name = "https://127.0.0.1/v=1234"

        link_data = {
            "link": link_name,
            "source_url": "https://youtube.com",
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
        }

        b = EntryDataBuilder()
        b.link_data = link_data
        # call tested function
        entry = b.build_from_props()

        objs = LinkDataController.objects.filter(link=link_name)
        self.assertEqual(objs.count(), 1)

        self.assertTrue(entry)
        self.assertTrue(entry.date_published is not None)
        self.assertTrue(entry.date_update_last is not None)

    def test_build_from_props__already_exists(self):
        config = Configuration.get_object().config_entry
        config.accept_non_domain_links = True
        config.accept_domain_links = False
        config.auto_create_sources = False
        config.auto_scan_new_entries = True
        config.save()

        EntryRules.objects.all().delete()

        MockRequestCounter.mock_page_requests = 0

        link_name = "https://youtube.com/v=1234"

        current_time = DateUtils.get_datetime_now_utc()
        creation_date = current_time - timedelta(days=1)

        first_created_entry = LinkDataController.objects.create(
            link=link_name, title="Title", description="Description"
        )

        link_data = {
            "link": link_name,
            "source_url": "https://youtube.com",
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": creation_date,
            "page_rating_contents": 23,
            "page_rating_votes": 12,
            "page_rating": 25,
        }

        b = EntryDataBuilder()
        b.user = self.user
        b.link_data = link_data
        # call tested function
        entry = b.build_from_props()

        self.assertEqual(first_created_entry, entry)

    def test_build_from_props__scan(self):
        config = Configuration.get_object().config_entry
        config.accept_non_domain_links = True
        config.accept_domain_links = False
        config.auto_create_sources = False
        config.auto_scan_new_entries = True
        config.save()

        EntryRules.objects.all().delete()

        MockRequestCounter.mock_page_requests = 0

        link_name = "https://youtube.com/v=1234"

        current_time = DateUtils.get_datetime_now_utc()
        creation_date = current_time - timedelta(days=1)

        link_data = {
            "link": link_name,
            "source_url": "https://youtube.com",
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": creation_date,
            "page_rating_contents": 23,
            "page_rating_votes": 12,
            "page_rating": 25,
        }

        b = EntryDataBuilder()
        b.user = self.user
        b.link_data = link_data
        # call tested function
        entry = b.build_from_props()

        objs = LinkDataController.objects.filter(link=link_name)

        self.assertEqual(objs.count(), 1)
        self.assertEqual(objs[0].link, link_name)

        scan_jobs = BackgroundJobController.objects.filter(
            job=BackgroundJobController.JOB_LINK_SCAN
        )
        self.assertEqual(scan_jobs.count(), 1)

    def test_build_from_props__too_long(self):
        config = Configuration.get_object().config_entry
        config.accept_non_domain_links = True
        config.accept_domain_links = False
        config.auto_scan_new_entries = True
        config.save()

        EntryRules.objects.all().delete()

        link_name = "https://youtube.com/v=1234/" + "0" * 1000

        link_data = {
            "link": link_name,
            "source_url": "https://youtube.com",
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": DateUtils.get_datetime_now_utc(),
        }

        b = EntryDataBuilder()
        b.link_data = link_data
        # call tested function
        entry = b.build_from_props()

        self.assertFalse(entry)

    def test_build_from_props__entry_rule__url_rejects(self):
        MockRequestCounter.mock_page_requests = 0

        config = Configuration.get_object().config_entry
        config.accept_non_domain_links = True
        config.accept_domain_links = False
        config.auto_scan_new_entries = True
        config.save()

        EntryRules.objects.create(trigger_rule_url="youtube.com", block=True)

        link_name = "https://youtube.com/v=1234"

        link_data = {
            "link": link_name,
            "source_url": "https://youtube.com",
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": DateUtils.get_datetime_now_utc(),
        }

        b = EntryDataBuilder()
        b.link_data = link_data
        # call tested function
        entry = b.build_from_props()

        objs = LinkDataController.objects.filter(link="https://youtube.com/v=1234")
        self.assertEqual(objs.count(), 0)

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_build_from_props__entry_rule__contents_rejects(self):
        MockRequestCounter.mock_page_requests = 0

        config = Configuration.get_object().config_entry
        config.accept_non_domain_links = True
        config.accept_domain_links = False
        config.auto_scan_new_entries = True
        config.save()

        EntryRules.objects.create(trigger_text="test", block=True)

        link_name = "https://youtube.com/v=1234"

        link_data = {
            "link": link_name,
            "source_url": "https://youtube.com",
            "title": "test test test test test test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": DateUtils.get_datetime_now_utc(),
        }

        b = EntryDataBuilder()
        b.link_data = link_data
        # call tested function
        entry = b.build_from_props()

        objs = LinkDataController.objects.filter(link="https://youtube.com/v=1234")
        self.assertEqual(objs.count(), 0)

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_build_from_props__status_code(self):
        config = Configuration.get_object().config_entry
        config.accept_non_domain_links = True
        config.accept_domain_links = False
        config.auto_create_sources = False
        config.auto_scan_new_entries = True
        config.save()

        EntryRules.objects.all().delete()

        MockRequestCounter.mock_page_requests = 0

        link_name = "https://youtube.com/v=1234"

        current_time = DateUtils.get_datetime_now_utc()
        creation_date = current_time - timedelta(days=1)

        link_data = {
            "link": link_name,
            "source_url": "https://youtube.com",
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": creation_date,
            "page_rating_contents": 23,
            "page_rating_votes": 12,
            "page_rating": 25,
            "status_code": 404,
        }

        b = EntryDataBuilder()
        b.user = self.user
        b.link_data = link_data
        # call tested function
        entry = b.build_from_props()

        self.assertFalse(entry)

    def test_build_from_link__valid(self):
        MockRequestCounter.mock_page_requests = 0

        config = Configuration.get_object().config_entry
        config.accept_non_domain_links = True
        config.accept_domain_links = False
        config.auto_scan_new_entries = True
        config.save()

        EntryRules.objects.all().delete()

        link_name = "https://youtube.com/v=1234"

        b = EntryDataBuilder()
        b.link = link_name
        # call tested function
        entry = b.build_from_link()

        objs = LinkDataController.objects.filter(link="https://youtube.com/v=1234")
        self.assertEqual(objs.count(), 1)

        self.assertEqual(MockRequestCounter.mock_page_requests, 1)

    def test_build_from_link__entry_rule__url_rejects(self):
        MockRequestCounter.mock_page_requests = 0

        config = Configuration.get_object().config_entry
        config.accept_non_domain_links = True
        config.accept_domain_links = False
        config.auto_scan_new_entries = True
        config.save()

        EntryRules.objects.create(trigger_rule_url="youtube.com", block=True)

        link_name = "https://youtube.com/v=1234"

        b = EntryDataBuilder()
        b.link = link_name
        # call tested function
        entry = b.build_from_link()

        objs = LinkDataController.objects.filter(link="https://youtube.com/v=1234")
        self.assertEqual(objs.count(), 0)

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_build_simple(self):
        config = Configuration.get_object().config_entry
        config.accept_non_domain_links = True
        config.accept_domain_links = False
        config.auto_create_sources = False
        config.auto_scan_new_entries = True
        config.save()

        EntryRules.objects.all().delete()

        MockRequestCounter.mock_page_requests = 0

        link_name = "https://youtube.com/v=1234"

        b = EntryDataBuilder()
        # call tested function
        entry = b.build_simple(link_name)

        objs = LinkDataController.objects.filter(link=link_name)

        self.assertEqual(objs.count(), 1)
        self.assertEqual(objs[0].link, link_name)
        self.assertFalse(objs[0].date_published)

        self.assertEqual(objs[0].page_rating_contents, 0)
        # votes are reset
        self.assertEqual(objs[0].page_rating_votes, 0)
        # visits are reset
        self.assertEqual(objs[0].page_rating_visits, 0)
        # rating is recalculated
        self.assertEqual(objs[0].page_rating, 0)

        # this is obtained not through page requests
        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_build_from_props__adds_scan(self):
        config = Configuration.get_object().config_entry
        config.accept_non_domain_links = True
        config.accept_domain_links = False
        config.auto_create_sources = False
        config.auto_scan_new_entries = True
        config.save()

        EntryRules.objects.all().delete()

        MockRequestCounter.mock_page_requests = 0

        link_name = "https://youtube.com/v=1234"

        current_time = DateUtils.get_datetime_now_utc()
        creation_date = current_time - timedelta(days=1)

        link_data = {
            "link": link_name,
            "source_url": "https://youtube.com",
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": creation_date,
            "page_rating_contents": 23,
            "page_rating_votes": 12,
            "page_rating": 25,
        }

        b = EntryDataBuilder()
        b.user = self.user
        b.link_data = link_data
        # call tested function
        entry = b.build_from_props()

        objs = BackgroundJobController.objects.filter(job = BackgroundJobController.JOB_LINK_SCAN)
        self.assertEqual(objs.count(), 1)
