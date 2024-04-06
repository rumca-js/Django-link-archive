from datetime import timedelta

from ..controllers import (
    LinkDataBuilder,
    LinkDataWrapper,
    SourceDataController,
    DomainsController,
)
from ..models import LinkDataModel
from ..dateutils import DateUtils
from ..configuration import Configuration

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class LinkDataBuilderTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()
        LinkDataModel.objects.all().delete()

    def test_add_from_props_no_slash(self):
        config = Configuration.get_object().config_entry
        config.auto_store_entries = True
        config.auto_store_domain_info = False
        config.auto_store_sources = False
        config.save()

        MockRequestCounter.mock_page_requests = 0

        link_name = "https://youtube.com/v=1234"

        current_time = DateUtils.get_datetime_now_utc()
        creation_date = current_time - timedelta(days=1)

        link_data = {
            "link": link_name,
            "source": "https://youtube.com",
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": creation_date,
            "page_rating_contents": 23,
            "page_rating_votes": 12,
            "page_rating": 25,
        }

        b = LinkDataBuilder()
        b.link_data = link_data
        # call tested function
        entry = b.add_from_props()

        objs = LinkDataModel.objects.filter(link=link_name)

        self.assertEqual(objs.count(), 1)
        self.assertEqual(objs[0].link, link_name)
        self.assertEqual(objs[0].date_published, creation_date)
        self.assertEqual(objs[0].page_rating_contents, 23)
        self.assertEqual(objs[0].page_rating_votes, 12)
        self.assertEqual(objs[0].page_rating, 25)

        # this is obtained not through page requests
        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_add_from_props_with_slash(self):
        config = Configuration.get_object().config_entry
        config.auto_store_entries = True
        config.auto_store_domain_info = False
        config.save()

        link_name = "https://youtube.com/v=1234/"

        link_data = {
            "link": link_name,
            "source": "https://youtube.com",
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": DateUtils.get_datetime_now_utc(),
        }

        b = LinkDataBuilder()
        b.link_data = link_data
        # call tested function
        entry = b.add_from_props()

        objs = LinkDataModel.objects.filter(link="https://youtube.com/v=1234/")
        self.assertEqual(objs.count(), 0)

        objs = LinkDataModel.objects.filter(link="https://youtube.com/v=1234")
        self.assertEqual(objs.count(), 1)

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_add_from_props_uppercase(self):
        config = Configuration.get_object().config_entry
        config.auto_store_entries = True
        config.auto_store_domain_info = False
        config.save()

        link_name = "HTTPS://YouTube.com/v=1234/"

        link_data = {
            "link": link_name,
            "source": "https://youtube.com",
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": DateUtils.get_datetime_now_utc(),
        }

        b = LinkDataBuilder()
        b.link_data = link_data
        # call tested function
        entry = b.add_from_props()

        objs = LinkDataModel.objects.filter(link="https://youtube.com/v=1234/")
        self.assertEqual(objs.count(), 0)

        objs = LinkDataModel.objects.filter(link="https://youtube.com/v=1234")
        self.assertEqual(objs.count(), 1)

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_add_from_props_not_adds(self):
        DomainsController.objects.all().delete()
        LinkDataModel.objects.all().delete()

        config = Configuration.get_object().config_entry
        config.auto_store_entries = False
        config.auto_store_domain_info = False
        config.save()

        objs = LinkDataModel.objects.all()
        self.assertEqual(objs.count(), 0)

        link_name_0 = "https://youtube.com/v=1234"

        link_data = {
            "link": link_name_0,
            "source": "https://youtube.com",
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": DateUtils.get_datetime_now_utc(),
            "bookmarked": False,
        }

        b = LinkDataBuilder(source_is_auto=True)
        b.link_data = link_data
        # call tested function
        entry = b.add_from_props()

        objs = LinkDataModel.objects.all()
        self.assertEqual(objs.count(), 0)

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_add_from_props_adds_domain(self):
        DomainsController.objects.all().delete()
        LinkDataModel.objects.all().delete()

        config = Configuration.get_object().config_entry
        config.auto_store_entries = False
        config.auto_store_domain_info = True
        config.save()

        link_name_0 = "https://youtube.com/v=1234"

        link_data = {
            "link": link_name_0,
            "source": "https://youtube.com",
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": DateUtils.get_datetime_now_utc(),
            "bookmarked": True,
        }

        b = LinkDataBuilder(source_is_auto=True)
        b.link_data = link_data
        # call tested function
        entry = b.add_from_props()

        objs = LinkDataModel.objects.all()
        domains = DomainsController.objects.all()

        for domain in domains:
            print("Domain:{}".format(domain.domain))

        # for each domain an entry is created
        self.assertEqual(objs.count(), 1)
        self.assertEqual(objs[0].link, "https://youtube.com")

        self.assertEqual(domains.count(), 1)
        self.assertEqual(objs[0].domain_obj, domains[0])

        link_name_1 = "https://youtube.com/v=1235"

        link_data = {
            "link": link_name_1,
            "source": "https://youtube.com",
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": DateUtils.get_datetime_now_utc(),
            "bookmarked": True,
        }

        b = LinkDataBuilder(source_is_auto=True)
        b.link_data = link_data
        # call tested function
        entry = b.add_from_props()

        objs = LinkDataModel.objects.all()
        domains = DomainsController.objects.all()

        # for each domain an entry is created
        self.assertEqual(objs.count(), 1)
        self.assertEqual(objs[0].link, "https://youtube.com")

        self.assertEqual(domains.count(), 1)

        self.assertEqual(objs[0].domain_obj, domains[0])

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_does_not_add_site_not_found(self):
        config = Configuration.get_object().config_entry
        config.auto_store_entries = True
        config.auto_store_domain_info = False
        config.auto_store_sources = False
        config.save()

        MockRequestCounter.mock_page_requests = 0

        link_name = "https://youtube.com/v=1234"

        current_time = DateUtils.get_datetime_now_utc()
        creation_date = current_time - timedelta(days=1)

        link_data = {
            "link": link_name,
            "source": "https://youtube.com",
            "title": "Site not found - GitHub",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": creation_date,
            "page_rating_contents": 23,
            "page_rating_votes": 12,
            "page_rating": 25,
        }

        b = LinkDataBuilder()
        b.link_data = link_data
        # call tested function
        entry = b.add_from_props()

        objs = LinkDataModel.objects.filter(link=link_name)
        self.assertEqual(objs.count(), 0)
