import django.utils
from django.test import TestCase
from datetime import timedelta

from ..controllers import (
    LinkDataBuilder,
    LinkDataWrapper,
    SourceDataController,
    DomainsController,
)
from ..models import ConfigurationEntry
from ..controllers import LinkDataController, ArchiveLinkDataController
from ..dateutils import DateUtils
from .utilities import WebPageDisabled
from ..configuration import Configuration


class UserObject(object):
    def __init__(self, user_name):
        self.username = user_name


class RequestObject(object):
    def __init__(self, user_name="TestUser"):
        self.user = UserObject(user_name)


class LinkDataWrapperTest(WebPageDisabled, TestCase):
    def setUp(self):
        self.disable_web_pages()
        self.source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )

    def test_make_bookmarked_now(self):
        link_name = "https://youtube.com/v=12345"

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
        entry = b.add_from_props()

        objs = LinkDataController.objects.filter(link=link_name)
        self.assertEqual(objs.count(), 1)
        obj = objs[0]

        # call tested function
        result = LinkDataWrapper.make_bookmarked(RequestObject(), obj)

        self.assertTrue(result)
        self.assertTrue(not result.is_archive_entry())

        objs = LinkDataController.objects.filter(link=link_name)
        self.assertEqual(objs.count(), 1)
        obj = objs[0]

        self.assertTrue(obj.bookmarked == True)

    def test_make_not_bookmarked_now(self):
        link_name = "https://youtube.com/v=12345"

        link_data = {
            "link": link_name,
            "source": "https://youtube.com",
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": DateUtils.get_datetime_now_utc(),
            "bookmarked": True,
        }

        b = LinkDataBuilder()
        b.link_data = link_data
        entry = b.add_from_props()

        objs = LinkDataController.objects.filter(link=link_name)
        self.assertEqual(objs.count(), 1)
        obj = objs[0]

        self.assertTrue(obj.bookmarked == True)

        # call tested function
        LinkDataWrapper.make_not_bookmarked(RequestObject(), obj)

        objs = LinkDataController.objects.filter(link=link_name)
        self.assertEqual(objs.count(), 1)
        obj = objs[0]

        self.assertTrue(obj.bookmarked == False)

    def test_move_to_archive(self):
        link_name = "https://youtube.com/v=12345"

        domain_obj = DomainsController.add("https://youtube.com")

        link_data = {
            "link": link_name,
            "source": "https://youtube.com",
            "domain_obj": domain_obj,
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": DateUtils.get_datetime_now_utc(),
        }

        obj = LinkDataController.objects.create(**link_data)
        self.assertTrue(obj)

        # call tested function
        result = LinkDataWrapper.move_to_archive(obj)

        self.assertTrue(result)
        self.assertTrue(result.is_archive_entry())
        self.assertEqual(result.domain_obj, domain_obj)

    def test_move_from_archive(self):
        link_name = "https://youtube.com/v=12345"

        domain_obj = DomainsController.add("https://youtube.com")

        link_data = {
            "link": link_name,
            "source": "https://youtube.com",
            "domain_obj": domain_obj,
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": DateUtils.get_datetime_now_utc() - timedelta(days=365),
        }

        obj = ArchiveLinkDataController.objects.create(**link_data)
        self.assertTrue(obj)

        LinkDataController.objects.all().delete()

        # call tested function
        result = LinkDataWrapper.move_from_archive(obj)

        self.assertTrue(result)
        self.assertTrue(not result.is_archive_entry())
        self.assertEqual(result.domain_obj, domain_obj)
