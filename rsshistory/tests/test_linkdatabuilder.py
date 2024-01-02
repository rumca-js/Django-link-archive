import django.utils
from django.test import TestCase
from datetime import timedelta

from ..controllers import (
    LinkDataBuilder,
    LinkDataWrapper,
    SourceDataController,
    DomainsController,
)
from ..models import LinkDataModel, ConfigurationEntry
from ..dateutils import DateUtils
from .utilities import WebPageDisabled
from ..configuration import Configuration


class UserObject(object):
    def __init__(self, user_name):
        self.username = user_name


class RequestObject(object):
    def __init__(self, user_name="TestUser"):
        self.user = UserObject(user_name)


class LinkDataBuilderTest(WebPageDisabled, TestCase):
    def setUp(self):
        self.disable_web_pages()
        self.source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )

    def test_add_new_link_no_slash(self):
        config = Configuration.get_object().config_entry
        config.auto_store_entries = True
        config.auto_store_domain_info = False
        config.save()

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
        }

        b = LinkDataBuilder()
        b.link_data = link_data
        # call tested function
        entry = b.add_from_props()

        objs = LinkDataModel.objects.filter(link=link_name)

        self.assertEqual(objs.count(), 1)
        self.assertEqual(objs[0].link, link_name)
        self.assertEqual(objs[0].date_published, creation_date)

    def test_add_new_link_with_slash(self):
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
        self.assertTrue(objs.count() == 0)

        objs = LinkDataModel.objects.filter(link="https://youtube.com/v=1234")
        self.assertTrue(objs.count() == 1)

    def test_add_new_link_not_adds(self):
        DomainsController.objects.all().delete()
        LinkDataModel.objects.all().delete()

        config = Configuration.get_object().config_entry
        # config = ConfigurationEntry.get()
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

        b = LinkDataBuilder(source_is_auto = True)
        b.link_data = link_data
        # call tested function
        entry = b.add_from_props()

        objs = LinkDataModel.objects.all()
        for obj in objs:
            print("Added {}".format(obj.link))
        self.assertEqual(objs.count(), 0)

    def test_add_new_link_adds_domain(self):
        DomainsController.objects.all().delete()
        LinkDataModel.objects.all().delete()

        config = Configuration.get_object().config_entry
        # config = ConfigurationEntry.get()
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

        b = LinkDataBuilder(source_is_auto = True)
        b.link_data = link_data
        # call tested function
        entry = b.add_from_props()

        objs = LinkDataModel.objects.filter(link=link_name_0)
        domains = DomainsController.objects.all()

        for domain in domains:
            print("Domain:{}".format(domain.domain))

        # for each domain an entry is created
        self.assertEqual(objs.count(), 1)
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

        b = LinkDataBuilder(source_is_auto = True)
        b.link_data = link_data
        # call tested function
        entry = b.add_from_props()

        objs = LinkDataModel.objects.all()
        domains = DomainsController.objects.all()

        # for each domain an entry is created
        self.assertEqual(objs.count(), 3)
        self.assertEqual(objs[0].link, link_name_1)
        self.assertEqual(objs[1].link, "https://youtube.com")
        self.assertEqual(objs[2].link, link_name_0)

        self.assertEqual(domains.count(), 1)

        self.assertEqual(objs[0].domain_obj, domains[0])
        self.assertEqual(objs[1].domain_obj, domains[0])
        self.assertEqual(objs[2].domain_obj, domains[0])
