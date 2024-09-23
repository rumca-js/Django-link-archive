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
)
from ..models import LinkDataModel
from ..configuration import Configuration

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class EntryDataBuilderTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        LinkDataController.objects.all().delete()
        ArchiveLinkDataController.objects.all().delete()

        self.user = User.objects.create_user(
            username="TestUser", password="testpassword", is_staff=True
        )

    def test_build_from_props_no_slash(self):
        config = Configuration.get_object().config_entry
        config.accept_not_domain_entries = True
        config.accept_domains = False
        config.auto_create_sources = False
        config.save()

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
        self.assertEqual(objs[0].user_object, self.user)

        self.assertEqual(objs[0].page_rating_contents, 23)
        # votes are reset
        self.assertEqual(objs[0].page_rating_votes, 0)
        # visits are reset
        self.assertEqual(objs[0].page_rating_visits, 0)
        # rating is recalculated
        self.assertEqual(objs[0].page_rating, 7)

        # this is obtained not through page requests
        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_build_from_props_with_slash(self):
        config = Configuration.get_object().config_entry
        config.accept_not_domain_entries = True
        config.accept_domains = False
        config.save()

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

    def test_build_from_props_uppercase(self):
        config = Configuration.get_object().config_entry
        config.accept_not_domain_entries = True
        config.accept_domains = False
        config.save()

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

    def test_build_from_props_not_adds(self):
        DomainsController.objects.all().delete()
        LinkDataController.objects.all().delete()

        config = Configuration.get_object().config_entry
        config.accept_not_domain_entries = False
        config.accept_domains = False
        config.save()

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

    def test_build_from_props_adds_domain(self):
        DomainsController.objects.all().delete()
        LinkDataController.objects.all().delete()

        config = Configuration.get_object().config_entry
        config.accept_not_domain_entries = False
        config.accept_domains = True
        config.save()

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

    def test_does_not_add_site_not_found(self):
        config = Configuration.get_object().config_entry
        config.accept_not_domain_entries = True
        config.accept_domains = False
        config.auto_create_sources = False
        config.save()

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
        b.link_data = link_data
        # call tested function
        entry = b.build_from_props()

        objs = LinkDataController.objects.filter(link=link_name)
        self.assertEqual(objs.count(), 0)

    def test_build_from_props__ipv4_rejects(self):
        config = Configuration.get_object().config_entry
        config.accept_not_domain_entries = True
        config.accept_domains = False
        config.auto_create_sources = False
        config.accept_ip_addresses = False
        config.save()

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
        config.accept_not_domain_entries = True
        config.accept_domains = False
        config.auto_create_sources = False
        config.accept_ip_addresses = True
        config.save()

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
        config.accept_not_domain_entries = True
        config.accept_domains = False
        config.auto_create_sources = False
        config.accept_ip_addresses = True
        config.save()

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
