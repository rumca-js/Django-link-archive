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
from ..configuration import Configuration

from .fakeinternet import FakeInternetTestCase


class UserObject(object):
    def __init__(self, user_name):
        self.username = user_name


class RequestObject(object):
    def __init__(self, user_name="TestUser"):
        self.user = UserObject(user_name)


class LinkDataWrapperTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )

    def clear(self):
        SourceDataController.objects.all().delete()
        LinkDataController.objects.all().delete()
        ArchiveLinkDataController.objects.all().delete()

    def create_entries(self, date_link_publish, date_to_remove):
        domain = DomainsController.objects.create(
            domain="https://youtube.com",
        )

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
            remove_after_days=1,
        )

        ob = LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=bookmarked",
            title="The first link",
            source_obj=source_youtube,
            bookmarked=True,
            language="en",
            domain_obj=domain,
            date_published=date_link_publish,
        )

        ob = LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=nonbookmarked",
            title="The second link",
            source_obj=source_youtube,
            bookmarked=False,
            language="en",
            domain_obj=domain,
            date_published=date_link_publish,
        )

        ob = LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=permanent",
            title="The first link",
            source_obj=source_youtube,
            permanent=True,
            language="en",
            domain_obj=domain,
            date_published=date_link_publish,
        )

        ob = ArchiveLinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=nonbookmarked2",
            title="The second link",
            source_obj=source_youtube,
            bookmarked=False,
            language="en",
            domain_obj=domain,
            date_published=date_to_remove,
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

    def test_clear_old_entries(self):
        conf = Configuration.get_object().config_entry

        current_time = DateUtils.get_datetime_now_utc()
        date_link_publish = current_time - timedelta(days=conf.days_to_remove_links + 2)
        date_to_remove = current_time - timedelta(days=conf.days_to_remove_links + 2)

        print("Date link publish")
        print(date_link_publish)
        print("Date to remove")
        print(date_to_remove)

        self.clear()
        self.create_entries(date_link_publish, date_to_remove)

        # call tested function
        LinkDataWrapper.clear_old_entries()

        bookmarked = LinkDataController.objects.filter(
            link="https://youtube.com?v=bookmarked"
        )
        self.assertEqual(bookmarked.count(), 1)

        permanent = LinkDataController.objects.filter(
            link="https://youtube.com?v=permanent"
        )
        self.assertEqual(permanent.count(), 1)

        nonbookmarked = LinkDataController.objects.filter(
            link="https://youtube.com?v=nonbookmarked"
        )
        self.assertEqual(nonbookmarked.count(), 0)

        self.assertEqual(ArchiveLinkDataController.objects.all().count(), 0)

    def test_move_old_links_to_archive(self):
        conf = Configuration.get_object().config_entry

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
        LinkDataWrapper.move_old_links_to_archive()

        bookmarked = LinkDataController.objects.filter(
            link="https://youtube.com?v=bookmarked"
        )
        self.assertEqual(bookmarked.count(), 1)

        permanent = LinkDataController.objects.filter(
            link="https://youtube.com?v=permanent"
        )
        self.assertEqual(permanent.count(), 1)

        nonbookmarked = LinkDataController.objects.filter(
            link="https://youtube.com?v=nonbookmarked"
        )
        self.assertEqual(nonbookmarked.count(), 0)

        archived = ArchiveLinkDataController.objects.all()
        domains = DomainsController.objects.all()

        self.assertEqual(archived.count(), 2)
        self.assertEqual(domains.count(), 1)

        self.assertEqual(archived[0].domain_obj, domains[0])
        self.assertEqual(archived[0].date_published, date_to_remove)

        self.assertEqual(archived[1].domain_obj, domains[0])
        self.assertEqual(archived[1].date_published, date_link_publish)
