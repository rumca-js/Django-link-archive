import django.utils

from django.test import TestCase

from ..controllers import LinkDataHyperController, SourceDataController
from ..models import LinkDataModel
from ..dateutils import DateUtils


class UserObject(object):
    def __init__(self, user_name):
        self.username = user_name


class RequestObject(object):
    def __init__(self, user_name="TestUser"):
        self.user = UserObject(user_name)


class SourceParsePluginTest(TestCase):
    def setUp(self):
        self.disable_web_pages()
        self.source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )

    def disable_web_pages(self):
        from ..webtools import BasePage, Page
        from ..models import ConfigurationEntry
        BasePage.user_agent = None
        Page.user_agent = None
        entry = ConfigurationEntry.get()
        entry.user_agent = ""
        entry.save()

    def test_add_new_link(self):
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

        link = LinkDataHyperController.add_new_link(link_data)

        objs = LinkDataModel.objects.filter(link=link_name)

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

        link = LinkDataHyperController.add_new_link(link_data)

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
