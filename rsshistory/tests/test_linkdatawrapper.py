from datetime import timedelta
from django.contrib.auth.models import User

from ..models import UserBookmarks
from ..controllers import (
    EntryDataBuilder,
    LinkDataWrapper,
    SourceDataController,
    DomainsController,
)
from ..controllers import LinkDataController, ArchiveLinkDataController
from ..dateutils import DateUtils
from ..configuration import Configuration

from .fakeinternet import FakeInternetTestCase, DjangoRequestObject


class LinkDataWrapperTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()
        self.setup_configuration()

        self.source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )

        self.user_staff = User.objects.create_user(
            username="TestUser", password="testpassword", is_staff=True
        )
        self.user_not_staff = User.objects.create_user(
            username="TestUserNot", password="testpassword", is_staff=False
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

        b = EntryDataBuilder()
        b.link_data = link_data
        entry = b.add_from_props()

        objs = LinkDataController.objects.filter(link=link_name)
        self.assertEqual(objs.count(), 1)
        obj = objs[0]

        # call tested function
        result = LinkDataWrapper(entry = obj).make_bookmarked(
            DjangoRequestObject(self.user_staff)
        )

        self.assertTrue(result)
        self.assertTrue(not result.is_archive_entry())

        objs = LinkDataController.objects.filter(link=link_name)
        self.assertEqual(objs.count(), 1)
        obj = objs[0]

        self.assertTrue(obj.bookmarked == True)

    def test_make_bookmarked_now_not_staff(self):
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

        b = EntryDataBuilder()
        b.link_data = link_data
        entry = b.add_from_props()

        objs = LinkDataController.objects.filter(link=link_name)
        self.assertEqual(objs.count(), 1)
        obj = objs[0]

        # call tested function
        result = LinkDataWrapper(entry = obj).make_bookmarked(
            DjangoRequestObject(self.user_not_staff),
        )

        self.assertTrue(result)
        self.assertTrue(not result.is_archive_entry())

        objs = LinkDataController.objects.filter(link=link_name)
        self.assertEqual(objs.count(), 1)
        obj = objs[0]

        self.assertTrue(obj.bookmarked == False)

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

        b = EntryDataBuilder()
        b.link_data = link_data
        entry = b.add_from_props()

        objs = LinkDataController.objects.filter(link=link_name)
        self.assertEqual(objs.count(), 1)
        obj = objs[0]

        self.assertTrue(obj.bookmarked == True)

        # call tested function
        LinkDataWrapper(entry = obj).make_not_bookmarked(DjangoRequestObject(self.user_staff))

        objs = LinkDataController.objects.filter(link=link_name)
        self.assertEqual(objs.count(), 1)
        obj = objs[0]

        self.assertTrue(obj.bookmarked == False)

    def test_make_bookmarked_staff(self):
        add_time = DateUtils.get_datetime_now_utc() - timedelta(days=1)

        entry = LinkDataController.objects.create(
            source="",
            link="https://linkedin.com",
            title="my title",
            description="my description",
            bookmarked=False,
            language="pl",
            domain_obj=None,
            date_published=add_time,
            thumbnail="thumbnail",
            source_obj=self.source_youtube,
        )

        date_updated = entry.date_update_last

        request = DjangoRequestObject(self.user_staff)

        # call tested function
        LinkDataWrapper(entry = entry).make_bookmarked(request)

        self.assertEqual(entry.bookmarked, True)
        self.assertEqual(UserBookmarks.objects.all().count(), 1)

    def test_make_bookmarked_not_staff(self):
        add_time = DateUtils.get_datetime_now_utc() - timedelta(days=1)

        entry = LinkDataController.objects.create(
            source="",
            link="https://linkedin.com",
            title="my title",
            description="my description",
            bookmarked=False,
            language="pl",
            domain_obj=None,
            date_published=add_time,
            thumbnail="thumbnail",
            source_obj=self.source_youtube,
        )

        date_updated = entry.date_update_last

        request = DjangoRequestObject(self.user_not_staff)

        # call tested function
        LinkDataWrapper(entry = entry).make_bookmarked(request)

        self.assertEqual(entry.bookmarked, False)
        self.assertEqual(UserBookmarks.objects.all().count(), 1)

    def test_make_not_bookmarked_staff(self):
        add_time = DateUtils.get_datetime_now_utc() - timedelta(days=1)

        entry = LinkDataController.objects.create(
            source="",
            link="https://linkedin.com",
            title="my title",
            description="my description",
            bookmarked=True,
            language="pl",
            domain_obj=None,
            date_published=add_time,
            thumbnail="thumbnail",
            source_obj=self.source_youtube,
        )

        date_updated = entry.date_update_last

        request = DjangoRequestObject(self.user_staff)

        # call tested function
        LinkDataWrapper(entry = entry).make_not_bookmarked(request)

        self.assertEqual(entry.bookmarked, False)
        self.assertEqual(UserBookmarks.objects.all().count(), 0)

    def test_make_not_bookmarked_not_staff(self):
        add_time = DateUtils.get_datetime_now_utc() - timedelta(days=1)

        entry = LinkDataController.objects.create(
            source="",
            link="https://linkedin.com",
            title="my title",
            description="my description",
            bookmarked=True,
            language="pl",
            domain_obj=None,
            date_published=add_time,
            thumbnail="thumbnail",
            source_obj=self.source_youtube,
        )

        date_updated = entry.date_update_last

        request = DjangoRequestObject(self.user_not_staff)

        # call tested function
        LinkDataWrapper(entry = entry).make_not_bookmarked(request)

        self.assertEqual(entry.bookmarked, False)
        self.assertEqual(UserBookmarks.objects.all().count(), 0)

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
        result = LinkDataWrapper(entry = obj).move_to_archive()

        self.assertTrue(result)
        self.assertTrue(result.is_archive_entry())
        self.assertEqual(result.domain_obj, domain_obj)

    def test_make_bookmarked_archived(self):
        link_name = "https://youtube.com/v=12345"

        link_data = {
            "link": link_name,
            "source": "https://youtube.com",
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": DateUtils.get_datetime_now_utc() - timedelta(days=365),
        }

        archive_entry = ArchiveLinkDataController.objects.create(**link_data)

        # call tested function
        result = LinkDataWrapper(entry = archive_entry).make_bookmarked(
            DjangoRequestObject(self.user_staff)
        )

        self.assertTrue(result)
        self.assertTrue(not result.is_archive_entry())

        objs = LinkDataController.objects.filter(link=link_name)
        self.assertEqual(objs.count(), 1)
        obj = objs[0]

        self.assertTrue(obj.bookmarked == True)

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
        result = LinkDataWrapper(entry = obj).move_from_archive()

        self.assertTrue(result)
        self.assertTrue(not result.is_archive_entry())
        self.assertEqual(result.domain_obj, domain_obj)

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
        self.assertEqual(archived[0].date_published, date_link_publish)

        self.assertEqual(archived[1].domain_obj, domains[0])
        self.assertEqual(archived[1].date_published, date_to_remove)

    def test_get_operational_db(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_move_to_archive = 2
        conf.days_to_remove_links = 2
        conf.days_to_remove_links = 2
        conf.prefer_https = True
        conf.save()

        ob = LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=1",
            title="The https link",
            bookmarked=False,
            language="en",
        )

        ob = LinkDataController.objects.create(
            source="http://youtube.com",
            link="http://youtube.com?v=1",
            title="The http link",
            bookmarked=False,
            language="en",
        )

        ob = ArchiveLinkDataController.objects.create(
            source="https://archive.com",
            link="https://archive.com?v=1",
            title="The archive https link",
            bookmarked=False,
            language="en",
        )

        ob = ArchiveLinkDataController.objects.create(
            source="http://archive.com",
            link="http://archive.com?v=1",
            title="The archive http link",
            bookmarked=False,
            language="en",
        )

        # call tested function
        w = LinkDataWrapper(link ="https://youtube.com?v=1")
        entry = w.get_from_operational_db()
        self.assertTrue(entry)
        self.assertEqual(entry.link, "https://youtube.com?v=1")

        # call tested function
        w = LinkDataWrapper(link = "http://youtube.com?v=1")
        entry = w.get_from_operational_db()
        self.assertTrue(entry)
        self.assertEqual(entry.link, "https://youtube.com?v=1")

        # call tested function
        w = LinkDataWrapper(link = "https://archive.com?v=1")
        entry = w.get_from_operational_db()
        self.assertTrue(not entry)

    def test_get_archive(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_move_to_archive = 2
        conf.days_to_remove_links = 2
        conf.days_to_remove_links = 2
        conf.prefer_https = True
        conf.save()

        ob = LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=1",
            title="The https link",
            bookmarked=False,
            language="en",
        )

        ob = LinkDataController.objects.create(
            source="http://youtube.com",
            link="http://youtube.com?v=1",
            title="The http link",
            bookmarked=False,
            language="en",
        )

        ob = ArchiveLinkDataController.objects.create(
            source="https://archive.com",
            link="https://archive.com?v=1",
            title="The archive https link",
            bookmarked=False,
            language="en",
        )

        ob = ArchiveLinkDataController.objects.create(
            source="http://archive.com",
            link="http://archive.com?v=1",
            title="The archive http link",
            bookmarked=False,
            language="en",
        )

        # call tested function
        w = LinkDataWrapper(link = "https://archive.com?v=1")
        entry = w.get_from_archive()
        self.assertTrue(entry)
        self.assertEqual(entry.link, "https://archive.com?v=1")

        # call tested function
        w = LinkDataWrapper(link = "http://archive.com?v=1")
        entry = w.get_from_archive()
        self.assertTrue(entry)
        self.assertEqual(entry.link, "https://archive.com?v=1")

    def test_check_https_http_protocol__http_link(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_move_to_archive = 2
        conf.days_to_remove_links = 2
        conf.days_to_remove_links = 2
        conf.prefer_https = True
        conf.save()

        https_entry = LinkDataController.objects.create(
            source="https://archive.com",
            link="https://archive.com?v=1",
            title="The archive https link",
            bookmarked=False,
            language="en",
        )

        http_entry = LinkDataController.objects.create(
            source="http://archive.com",
            link="http://archive.com?v=1",
            title="The archive http link",
            bookmarked=False,
            language="en",
        )

        # call tested function
        result = LinkDataWrapper(entry = http_entry).check_https_http_protocol()
        self.assertTrue(result)

        # function removed http link

        entries = LinkDataController.objects.filter(link__icontains = "archive.com")
        self.assertEqual(entries.count(), 1)
        self.assertEqual(entries[0].link, "https://archive.com?v=1")

    def test_check_https_http_protocol__https_link(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_move_to_archive = 2
        conf.days_to_remove_links = 2
        conf.days_to_remove_links = 2
        conf.prefer_https = True
        conf.save()

        https_entry = LinkDataController.objects.create(
            source="https://archive.com",
            link="https://archive.com?v=1",
            title="The archive https link",
            bookmarked=False,
            language="en",
        )

        http_entry = LinkDataController.objects.create(
            source="http://archive.com",
            link="http://archive.com?v=1",
            title="The archive http link",
            bookmarked=False,
            language="en",
        )

        # call tested function
        result = LinkDataWrapper(entry = https_entry).check_https_http_protocol()
        self.assertTrue(not result)

        # function removed http link

        entries = LinkDataController.objects.filter(link__icontains = "archive.com")
        self.assertEqual(entries.count(), 1)
        self.assertEqual(entries[0].link, "https://archive.com?v=1")

    def test_check_https_http_protocol__https_link_dead(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_move_to_archive = 2
        conf.days_to_remove_links = 2
        conf.days_to_remove_links = 2
        conf.prefer_https = True
        conf.save()

        https_entry = LinkDataController.objects.create(
            source="https://archive.com",
            link="https://archive.com?v=1",
            title="The archive https link",
            bookmarked=False,
            language="en",
            date_dead_since = DateUtils.get_datetime_now_utc(),
        )

        # call tested function
        result = LinkDataWrapper(entry = https_entry).check_https_http_protocol()

        # we do not move the thing
        self.assertFalse(result)

        # we still use https, if we have server reponse for it

        entries = LinkDataController.objects.filter(link__icontains = "archive.com")
        self.assertEqual(entries.count(), 1)
        self.assertEqual(entries[0].link, "https://archive.com?v=1")

    def test_evaluate__removes_entry_domain(self):
        LinkDataController.objects.all().delete()

        conf = Configuration.get_object().config_entry
        conf.days_to_move_to_archive = 2
        conf.days_to_remove_links = 2
        conf.auto_store_domains = False
        conf.auto_store_entries = False
        conf.prefer_https = True
        conf.save()

        https_entry = LinkDataController.objects.create(
            source="https://archive.com",
            link="https://archive.com",
            title="The archive https link",
            bookmarked=False,
            language="en",
            date_dead_since = DateUtils.get_datetime_now_utc() - timedelta(days=5),
            date_published = DateUtils.get_datetime_now_utc() - timedelta(days=5),
        )

        # call tested function
        result = LinkDataWrapper(entry = https_entry).evaluate()

        entries = LinkDataController.objects.filter(link__icontains = "archive.com")
        self.assertEqual(entries.count(), 0)

        entries = ArchiveLinkDataController.objects.filter(link__icontains = "archive.com")
        self.assertEqual(entries.count(), 0)

    def test_evaluate__removes_entry_not_domain(self):
        LinkDataController.objects.all().delete()

        conf = Configuration.get_object().config_entry
        conf.days_to_move_to_archive = 2
        conf.days_to_remove_links = 2
        conf.auto_store_domains = False
        conf.auto_store_entries = False
        conf.prefer_https = True
        conf.save()

        https_entry = LinkDataController.objects.create(
            source="https://archive.com/test",
            link="https://archive.com?v=1",
            title="The archive https link",
            bookmarked=False,
            language="en",
            date_dead_since = DateUtils.get_datetime_now_utc() - timedelta(days=5),
            date_published = DateUtils.get_datetime_now_utc() - timedelta(days=5),
        )

        # call tested function
        result = LinkDataWrapper(entry = https_entry).evaluate()

        entries = LinkDataController.objects.filter(link__icontains = "archive.com")
        self.assertEqual(entries.count(), 0)

        entries = ArchiveLinkDataController.objects.filter(link__icontains = "archive.com")
        self.assertEqual(entries.count(), 0)

    def test_evaluate__moves_entry(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_move_to_archive = 2
        conf.days_to_remove_links = 5
        conf.auto_store_domains = False
        conf.auto_store_entries = True
        conf.prefer_https = True
        conf.save()

        https_entry = LinkDataController.objects.create(
            source="https://archive.com/test",
            link="https://archive.com?v=1",
            title="The archive https link",
            bookmarked=False,
            language="en",
            date_dead_since = DateUtils.get_datetime_now_utc() - timedelta(days=3),
            date_published = DateUtils.get_datetime_now_utc() - timedelta(days=3),
        )

        # call tested function
        result = LinkDataWrapper(entry = https_entry).evaluate()

        entries = LinkDataController.objects.filter(link__icontains = "archive.com")
        self.assertEqual(entries.count(), 0)

        entries = ArchiveLinkDataController.objects.filter(link__icontains = "archive.com")
        self.assertEqual(entries.count(), 1)
