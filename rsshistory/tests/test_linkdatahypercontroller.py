import datetime

from django.test import TestCase

from ..controllers import LinkDataHyperController, SourceDataController

from ..models import LinkDataModel


class UserObject(object):
    def __init__(self, user_name):
        self.username = user_name


class RequestObject(object):
    def __init__(self, user_name="TestUser"):
        self.user = UserObject(user_name)


class SourceParsePluginTest(TestCase):
    def setUp(self):
        self.source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )

    def test_add_new_link(self):
        link_name = "https://youtube.com/v=1234"

        link_data = {
            "link": link_name,
            "source": "https://youtube.com",
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": datetime.datetime.now(),
        }

        link = LinkDataHyperController.add_new_link(link_data)

        objs = LinkDataModel.objects.filter(link=link_name)

        self.assertTrue(len(objs) == 1)

    def test_make_persistent(self):
        link_name = "https://youtube.com/v=12345"

        link_data = {
            "link": link_name,
            "source": "https://youtube.com",
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": datetime.datetime.now(),
        }

        link = LinkDataHyperController.add_new_link(link_data)

        objs = LinkDataModel.objects.filter(link=link_name)
        obj = objs[0]

        LinkDataHyperController.make_persistent(RequestObject(), obj)

        objs = LinkDataModel.objects.filter(link=link_name)
        obj = objs[0]

        self.assertTrue(obj.persistent == True)

        LinkDataHyperController.make_not_persistent(RequestObject(), obj)

        objs = LinkDataModel.objects.filter(link=link_name)
        obj = objs[0]

        self.assertTrue(obj.persistent == False)