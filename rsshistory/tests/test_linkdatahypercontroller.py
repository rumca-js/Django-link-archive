import django.utils

from django.test import TestCase

from ..controllers import LinkDataHyperController, SourceDataController, DomainsController
from ..models import LinkDataModel, ConfigurationEntry
from ..dateutils import DateUtils
from .utilities import WebPageDisabled


class UserObject(object):
    def __init__(self, user_name):
        self.username = user_name


class RequestObject(object):
    def __init__(self, user_name="TestUser"):
        self.user = UserObject(user_name)


class SourceParsePluginTest(WebPageDisabled, TestCase):
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
        link_name = "https://youtube.com/v=1234"

        link_data = {
            "link": link_name,
            "source": "https://youtube.com",
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": DateUtils.get_datetime_now_utc(),
        }

        entry = LinkDataHyperController.add_new_link(link_data)

        objs = LinkDataModel.objects.filter(link=link_name)

        self.assertTrue(objs.count() == 1)

    def test_add_new_link_with_slash(self):
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

        entry = LinkDataHyperController.add_new_link(link_data)

        objs = LinkDataModel.objects.filter(link="https://youtube.com/v=1234/")
        self.assertTrue(objs.count() == 0)

        objs = LinkDataModel.objects.filter(link="https://youtube.com/v=1234")
        self.assertTrue(objs.count() == 1)

    def test_make_bookmarked(self):
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

        entry = LinkDataHyperController.add_new_link(link_data)

        objs = LinkDataModel.objects.filter(link=link_name)
        self.assertEqual(objs.count(), 1)
        obj = objs[0]

        LinkDataHyperController.make_bookmarked(RequestObject(), obj)

        objs = LinkDataModel.objects.filter(link=link_name)
        self.assertEqual(objs.count(), 1)
        obj = objs[0]

        self.assertTrue(obj.bookmarked == True)

        LinkDataHyperController.make_not_bookmarked(RequestObject(), obj)

        objs = LinkDataModel.objects.filter(link=link_name)
        self.assertEqual(objs.count(), 1)
        obj = objs[0]

        self.assertTrue(obj.bookmarked == False)

    def test_add_new_link_adds_domain(self):
        DomainsController.objects.all().delete()
        LinkDataModel.objects.all().delete()

        config = ConfigurationEntry.get()
        config.auto_store_entries = False
        config.auto_store_domain_info = True
        config.save()

        link_name = "https://youtube.com/v=1234"

        link_data = {
            "link": link_name,
            "source": "https://youtube.com",
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": DateUtils.get_datetime_now_utc(),
        }

        entry = LinkDataHyperController.add_new_link(link_data, source_is_auto=True)

        objs = LinkDataModel.objects.filter(link=link_name)

        # for each domain an entry is created
        self.assertEqual(objs.count(), 1)
        self.assertEqual(DomainsController.objects.all().count(), 1)
