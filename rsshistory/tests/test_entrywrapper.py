from datetime import timedelta
from django.contrib.auth.models import User

from utils.dateutils import DateUtils

from ..models import (
    UserBookmarks,
    UserTags,
    UserVotes,
    UserComments,
    UserBookmarks,
    UserEntryTransitionHistory,
    UserEntryVisitHistory,
)
from ..controllers import (
    EntryDataBuilder,
    EntryWrapper,
    SourceDataController,
    DomainsController,
)
from ..controllers import LinkDataController, ArchiveLinkDataController
from ..configuration import Configuration

from .fakeinternet import FakeInternetTestCase, DjangoRequestObject


class EntryWrapperTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()
        self.setup_configuration()

        c = Configuration.get_object()
        c.config_entry.track_user_actions = True
        c.config_entry.track_user_searches = True
        c.config_entry.track_user_navigation = True
        c.config_entry.save()

        self.source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
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
            export_to_cms=True,
            remove_after_days=1,
        )

        ob = LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=bookmarked",
            title="The first link",
            source=source_youtube,
            bookmarked=True,
            language="en",
            domain=domain,
            date_published=date_link_publish,
        )

        ob = LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=nonbookmarked",
            title="The second link",
            source=source_youtube,
            bookmarked=False,
            language="en",
            domain=domain,
            date_published=date_link_publish,
        )

        ob = LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=permanent",
            title="The first link",
            source=source_youtube,
            permanent=True,
            language="en",
            domain=domain,
            date_published=date_link_publish,
        )

        ob = ArchiveLinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=nonbookmarked2",
            title="The second link",
            source=source_youtube,
            bookmarked=False,
            language="en",
            domain=domain,
            date_published=date_to_remove,
        )

    def test_make_bookmarked_now(self):
        link_name = "https://youtube.com/v=12345"

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
        entry = b.build_from_props()

        objs = LinkDataController.objects.filter(link=link_name)
        self.assertEqual(objs.count(), 1)
        obj = objs[0]

        # call tested function
        result = EntryWrapper(entry=obj).make_bookmarked(
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
            "source_url": "https://youtube.com",
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": DateUtils.get_datetime_now_utc(),
        }

        b = EntryDataBuilder()
        b.link_data = link_data
        entry = b.build_from_props()

        objs = LinkDataController.objects.filter(link=link_name)
        self.assertEqual(objs.count(), 1)
        obj = objs[0]

        # call tested function
        result = EntryWrapper(entry=obj).make_bookmarked(
            DjangoRequestObject(self.user_not_staff),
        )

        self.assertTrue(result)
        self.assertTrue(not result.is_archive_entry())

        objs = LinkDataController.objects.filter(link=link_name)
        self.assertEqual(objs.count(), 1)
        obj = objs[0]

        self.assertTrue(obj.bookmarked == True)

    def test_make_not_bookmarked__now(self):
        link_name = "https://youtube.com/v=12345"

        link_data = {
            "link": link_name,
            "source_url": "https://youtube.com",
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": DateUtils.get_datetime_now_utc(),
            "bookmarked": True,
        }

        b = EntryDataBuilder()
        b.link_data = link_data
        entry = b.build_from_props()

        objs = LinkDataController.objects.filter(link=link_name)
        self.assertEqual(objs.count(), 1)
        obj = objs[0]

        self.assertTrue(obj.bookmarked == True)

        # call tested function
        EntryWrapper(entry=obj).make_not_bookmarked(
            DjangoRequestObject(self.user_staff)
        )

        objs = LinkDataController.objects.filter(link=link_name)
        self.assertEqual(objs.count(), 1)
        obj = objs[0]

        self.assertTrue(obj.bookmarked == False)

    def test_make_bookmarked__staff(self):
        add_time = DateUtils.get_datetime_now_utc() - timedelta(days=1)

        entry = LinkDataController.objects.create(
            source_url="",
            link="https://linkedin.com",
            title="my title",
            description="my description",
            bookmarked=False,
            language="pl",
            domain=None,
            date_published=add_time,
            thumbnail="thumbnail",
            source=self.source_youtube,
        )

        date_updated = entry.date_update_last

        request = DjangoRequestObject(self.user_staff)

        # call tested function
        EntryWrapper(entry=entry).make_bookmarked(request)

        self.assertEqual(entry.bookmarked, True)
        self.assertEqual(UserBookmarks.objects.all().count(), 1)

    def test_make_bookmarked__not_staff(self):
        add_time = DateUtils.get_datetime_now_utc() - timedelta(days=1)

        entry = LinkDataController.objects.create(
            source_url="",
            link="https://linkedin.com",
            title="my title",
            description="my description",
            bookmarked=False,
            language="pl",
            domain=None,
            date_published=add_time,
            thumbnail="thumbnail",
            source=self.source_youtube,
        )

        date_updated = entry.date_update_last

        request = DjangoRequestObject(self.user_not_staff)

        # call tested function
        EntryWrapper(entry=entry).make_bookmarked(request)

        self.assertEqual(entry.bookmarked, True)
        self.assertEqual(UserBookmarks.objects.all().count(), 1)

    def test_make_not_bookmarked__staff(self):
        add_time = DateUtils.get_datetime_now_utc() - timedelta(days=1)

        entry = LinkDataController.objects.create(
            source_url="",
            link="https://linkedin.com",
            title="my title",
            description="my description",
            bookmarked=True,
            language="pl",
            domain=None,
            date_published=add_time,
            thumbnail="thumbnail",
            source=self.source_youtube,
        )

        date_updated = entry.date_update_last

        request = DjangoRequestObject(self.user_staff)

        # call tested function
        EntryWrapper(entry=entry).make_not_bookmarked(request)

        self.assertEqual(entry.bookmarked, False)
        self.assertEqual(UserBookmarks.objects.all().count(), 0)

    def test_make_not_bookmarked__not_staff(self):
        add_time = DateUtils.get_datetime_now_utc() - timedelta(days=1)

        entry = LinkDataController.objects.create(
            source_url="",
            link="https://linkedin.com",
            title="my title",
            description="my description",
            bookmarked=True,
            language="pl",
            domain=None,
            date_published=add_time,
            thumbnail="thumbnail",
            source=self.source_youtube,
        )

        date_updated = entry.date_update_last

        request = DjangoRequestObject(self.user_not_staff)

        # call tested function
        EntryWrapper(entry=entry).make_not_bookmarked(request)

        self.assertEqual(entry.bookmarked, False)
        self.assertEqual(UserBookmarks.objects.all().count(), 0)

    def test_move_to_archive(self):
        link_name = "https://youtube.com/v=12345"

        domain_obj = DomainsController.add("https://youtube.com")

        link_data = {
            "link": link_name,
            "source_url": "https://youtube.com",
            "domain": domain_obj,
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": DateUtils.get_datetime_now_utc(),
        }

        obj = LinkDataController.objects.create(**link_data)
        self.assertTrue(obj)

        # call tested function
        result = EntryWrapper(entry=obj).move_to_archive()

        self.assertTrue(result)
        self.assertTrue(result.is_archive_entry())
        self.assertEqual(result.domain, domain_obj)

    def test_make_bookmarked_archived(self):
        link_name = "https://youtube.com/v=12345"

        link_data = {
            "link": link_name,
            "source_url": "https://youtube.com",
            "title": "test",
            "description": "description",
            "language": "en",
            "thumbnail": "https://youtube.com/favicon.ico",
            "date_published": DateUtils.get_datetime_now_utc() - timedelta(days=365),
        }

        archive_entry = ArchiveLinkDataController.objects.create(**link_data)

        # call tested function
        result = EntryWrapper(entry=archive_entry).make_bookmarked(
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
            "source_url": "https://youtube.com",
            "domain": domain_obj,
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
        result = EntryWrapper(entry=obj).move_from_archive()

        self.assertTrue(result)
        self.assertTrue(not result.is_archive_entry())
        self.assertEqual(result.domain, domain_obj)

    def test_get_from_db__linkdatacontroller(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_move_to_archive = 2
        conf.days_to_remove_links = 2
        conf.days_to_remove_links = 2
        conf.prefer_https = True
        conf.save()

        LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=1",
            title="The https link",
            bookmarked=False,
            language="en",
        )

        LinkDataController.objects.create(
            source_url="http://youtube.com",
            link="http://youtube.com?v=1",
            title="The http link",
            bookmarked=False,
            language="en",
        )

        ArchiveLinkDataController.objects.create(
            source_url="https://archive.com",
            link="https://archive.com?v=1",
            title="The archive https link",
            bookmarked=False,
            language="en",
        )

        ArchiveLinkDataController.objects.create(
            source_url="http://archive.com",
            link="http://archive.com?v=1",
            title="The archive http link",
            bookmarked=False,
            language="en",
        )

        w = EntryWrapper(link="https://youtube.com?v=1")
        # call tested function
        entry = w.get_from_db(LinkDataController.objects)
        self.assertTrue(entry)
        self.assertEqual(entry.link, "https://youtube.com?v=1")

        w = EntryWrapper(link="http://youtube.com?v=1")
        # call tested function
        entry = w.get_from_db(LinkDataController.objects)
        self.assertTrue(entry)
        self.assertEqual(entry.link, "https://youtube.com?v=1")

        w = EntryWrapper(link="http://www.youtube.com?v=1")
        # call tested function
        entry = w.get_from_db(LinkDataController.objects)
        self.assertTrue(entry)
        self.assertEqual(entry.link, "https://youtube.com?v=1")

        w = EntryWrapper(link="https://archive.com?v=1")
        # call tested function
        entry = w.get_from_db(LinkDataController.objects)
        self.assertTrue(not entry)

    def test_get_from_db__archivelinkdatacontroller(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_move_to_archive = 2
        conf.days_to_remove_links = 2
        conf.days_to_remove_links = 2
        conf.prefer_https = True
        conf.save()

        ob = LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=1",
            title="The https link",
            bookmarked=False,
            language="en",
        )

        ob = LinkDataController.objects.create(
            source_url="http://youtube.com",
            link="http://youtube.com?v=1",
            title="The http link",
            bookmarked=False,
            language="en",
        )

        ob = ArchiveLinkDataController.objects.create(
            source_url="https://archive.com",
            link="https://archive.com?v=1",
            title="The archive https link",
            bookmarked=False,
            language="en",
        )

        ob = ArchiveLinkDataController.objects.create(
            source_url="http://archive.com",
            link="http://archive.com?v=1",
            title="The archive http link",
            bookmarked=False,
            language="en",
        )

        w = EntryWrapper(link="https://archive.com?v=1")
        # call tested function
        entry = w.get_from_db(ArchiveLinkDataController.objects)
        self.assertTrue(entry)
        self.assertEqual(entry.link, "https://archive.com?v=1")

        w = EntryWrapper(link="http://archive.com?v=1")
        # call tested function
        entry = w.get_from_db(ArchiveLinkDataController.objects)
        self.assertTrue(entry)
        self.assertEqual(entry.link, "https://archive.com?v=1")

        w = EntryWrapper(link="http://www.archive.com?v=1")
        # call tested function
        entry = w.get_from_db(ArchiveLinkDataController.objects)
        self.assertTrue(entry)
        self.assertEqual(entry.link, "https://archive.com?v=1")

    def test_get(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_move_to_archive = 2
        conf.days_to_remove_links = 2
        conf.days_to_remove_links = 2
        conf.prefer_https = True
        conf.save()

        LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=1",
            title="The https link",
            bookmarked=False,
            language="en",
        )

        LinkDataController.objects.create(
            source_url="http://youtube.com",
            link="http://youtube.com?v=1",
            title="The http link",
            bookmarked=False,
            language="en",
        )

        ArchiveLinkDataController.objects.create(
            source_url="https://archive.com",
            link="https://archive.com?v=1",
            title="The archive https link",
            bookmarked=False,
            language="en",
        )

        ArchiveLinkDataController.objects.create(
            source_url="http://archive.com",
            link="http://archive.com?v=1",
            title="The archive http link",
            bookmarked=False,
            language="en",
        )

        w = EntryWrapper(link="https://youtube.com?v=1")
        # call tested function
        entry = w.get()
        self.assertTrue(entry)
        self.assertEqual(entry.link, "https://youtube.com?v=1")

        w = EntryWrapper(link="https://archive.com?v=1")
        # call tested function
        entry = w.get()
        self.assertTrue(entry)

    def test_check_https_http_availability__http_link(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_move_to_archive = 2
        conf.days_to_remove_links = 2
        conf.days_to_remove_links = 2
        conf.prefer_https = True
        conf.save()

        https_entry = LinkDataController.objects.create(
            source_url="https://archive.com",
            link="https://archive.com?v=1",
            title="The archive https link",
            bookmarked=False,
            language="en",
        )

        http_entry = LinkDataController.objects.create(
            source_url="http://archive.com",
            link="http://archive.com?v=1",
            title="The archive http link",
            bookmarked=False,
            language="en",
        )

        # call tested function
        result = EntryWrapper(entry=http_entry).check_https_http_availability()
        self.assertTrue(result)

        # function removed http link

        entries = LinkDataController.objects.filter(link__icontains="archive.com")
        self.assertEqual(entries.count(), 1)
        self.assertEqual(entries[0].link, "https://archive.com?v=1")

    def test_check_https_http_availability__https_link(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_move_to_archive = 2
        conf.days_to_remove_links = 2
        conf.days_to_remove_links = 2
        conf.prefer_https = True
        conf.save()

        https_entry = LinkDataController.objects.create(
            source_url="https://archive.com",
            link="https://archive.com?v=1",
            title="The archive https link",
            bookmarked=False,
            language="en",
        )

        http_entry = LinkDataController.objects.create(
            source_url="http://archive.com",
            link="http://archive.com?v=1",
            title="The archive http link",
            bookmarked=False,
            language="en",
        )

        # call tested function
        entry = EntryWrapper(entry=https_entry).check_https_http_availability()
        self.assertEqual(entry, https_entry)

        # function removed http link

        entries = LinkDataController.objects.filter(link__icontains="archive.com")
        self.assertEqual(entries.count(), 1)
        self.assertEqual(entries[0].link, "https://archive.com?v=1")

    def test_check_https_http_availability__https_link_dead(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_move_to_archive = 2
        conf.days_to_remove_links = 2
        conf.days_to_remove_links = 2
        conf.prefer_https = True
        conf.save()

        https_entry = LinkDataController.objects.create(
            source_url="https://archive.com",
            link="https://archive.com?v=1",
            title="The archive https link",
            bookmarked=False,
            language="en",
            date_dead_since=DateUtils.get_datetime_now_utc(),
        )

        # call tested function
        entry = EntryWrapper(entry=https_entry).check_https_http_availability()

        # we do not move the thing
        self.assertEqual(entry, https_entry)

        # we still use https, if we have server reponse for it

        entries = LinkDataController.objects.filter(link__icontains="archive.com")
        self.assertEqual(entries.count(), 1)
        self.assertEqual(entries[0].link, "https://archive.com?v=1")

    def test_evaluate__removes_entry_domain(self):
        LinkDataController.objects.all().delete()

        conf = Configuration.get_object().config_entry
        conf.days_to_move_to_archive = 2
        conf.days_to_remove_links = 2
        conf.accept_domain_links = False
        conf.accept_non_domain_links = False
        conf.prefer_https = True
        conf.save()

        https_entry = LinkDataController.objects.create(
            source_url="https://archive.com",
            link="https://archive.com",
            title="The archive https link",
            bookmarked=False,
            language="en",
            date_dead_since=DateUtils.get_datetime_now_utc() - timedelta(days=5),
            date_published=DateUtils.get_datetime_now_utc() - timedelta(days=5),
        )

        # call tested function
        result = EntryWrapper(entry=https_entry).evaluate()

        entries = LinkDataController.objects.filter(link__icontains="archive.com")
        self.assertEqual(entries.count(), 0)

        entries = ArchiveLinkDataController.objects.filter(
            link__icontains="archive.com"
        )
        self.assertEqual(entries.count(), 0)

    def test_evaluate__removes_entry_not_domain(self):
        LinkDataController.objects.all().delete()

        conf = Configuration.get_object().config_entry
        conf.days_to_move_to_archive = 2
        conf.days_to_remove_links = 2
        conf.accept_domain_links = False
        conf.accept_non_domain_links = False
        conf.prefer_https = True
        conf.save()

        https_entry = LinkDataController.objects.create(
            source_url="https://archive.com/test",
            link="https://archive.com?v=1",
            title="The archive https link",
            bookmarked=False,
            language="en",
            date_dead_since=DateUtils.get_datetime_now_utc() - timedelta(days=5),
            date_published=DateUtils.get_datetime_now_utc() - timedelta(days=5),
        )

        # call tested function
        result = EntryWrapper(entry=https_entry).evaluate()

        entries = LinkDataController.objects.filter(link__icontains="archive.com")
        self.assertEqual(entries.count(), 0)

        entries = ArchiveLinkDataController.objects.filter(
            link__icontains="archive.com"
        )
        self.assertEqual(entries.count(), 0)

    def test_evaluate__moves_entry(self):
        conf = Configuration.get_object().config_entry
        conf.days_to_move_to_archive = 2
        conf.days_to_remove_links = 5
        conf.accept_domain_links = False
        conf.accept_non_domain_links = True
        conf.prefer_https = True
        conf.save()

        https_entry = LinkDataController.objects.create(
            source_url="https://archive.com/test",
            link="https://archive.com?v=1",
            title="The archive https link",
            bookmarked=False,
            language="en",
            date_dead_since=DateUtils.get_datetime_now_utc() - timedelta(days=3),
            date_published=DateUtils.get_datetime_now_utc() - timedelta(days=3),
        )

        # call tested function
        result = EntryWrapper(entry=https_entry).evaluate()

        entries = LinkDataController.objects.filter(link__icontains="archive.com")
        self.assertEqual(entries.count(), 0)

        entries = ArchiveLinkDataController.objects.filter(
            link__icontains="archive.com"
        )
        self.assertEqual(entries.count(), 1)

    def test_move_entry__destination_exists(self):
        https_entry = LinkDataController.objects.create(
            source_url="https://archive.com/test",
            link="https://testlink.com",
            title="The archive https link",
            bookmarked=True,
            language="en",
            date_published=DateUtils.get_datetime_now_utc() - timedelta(days=3),
        )

        http_entry = LinkDataController.objects.create(
            source_url="http://archive.com/test",
            link="http://testlink.com",
            title="The archive https link",
            bookmarked=True,
            language="en",
            date_published=DateUtils.get_datetime_now_utc() - timedelta(days=3),
        )

        youtube_entry = LinkDataController.objects.create(
            source_url="http://youtube.com/test",
            link="http://youtube.com?v=1",
            title="The archive https link",
            bookmarked=True,
            language="en",
            date_published=DateUtils.get_datetime_now_utc() - timedelta(days=3),
        )

        UserTags.set_tag(http_entry, "test", self.user_not_staff)
        UserVotes.add(self.user_not_staff, http_entry, 30)
        UserComments.add(self.user_not_staff, http_entry, "This is stupid")
        UserBookmarks.add(self.user_not_staff, http_entry)

        UserEntryVisitHistory.visited(http_entry, self.user_not_staff)
        UserEntryVisitHistory.visited(youtube_entry, self.user_not_staff)

        # verify before call

        tags = UserTags.objects.all()
        self.assertEqual(tags.count(), 1)

        all_transitions = UserEntryTransitionHistory.objects.all()
        self.assertEqual(all_transitions.count(), 1)
        transition = all_transitions[0]
        self.assertEqual(transition.entry_from, http_entry)
        self.assertEqual(transition.entry_to, youtube_entry)

        # call tested function
        result = EntryWrapper(entry=http_entry).move_entry(https_entry)

        # Check expected behavior

        self.print_errors()

        https_entries = LinkDataController.objects.filter(link="https://testlink.com")
        http_entries = LinkDataController.objects.filter(link="http://testlink.com")

        self.assertEqual(https_entries.count(), 1)
        self.assertEqual(http_entries.count(), 0)

        tags = UserTags.objects.all()
        self.assertEqual(tags.count(), 1)
        tag = tags[0]
        self.assertEqual(tag.entry, https_entry)

        votes = UserVotes.objects.all()
        self.assertEqual(votes.count(), 1)
        vote = votes[0]
        self.assertEqual(vote.entry, https_entry)

        comments = UserComments.objects.all()
        self.assertEqual(comments.count(), 1)
        comment = comments[0]
        self.assertEqual(comment.entry, https_entry)

        bookmarks = UserBookmarks.objects.all()
        self.assertEqual(bookmarks.count(), 1)
        bookmark = bookmarks[0]
        self.assertEqual(bookmark.entry, https_entry)

        all_transitions = UserEntryTransitionHistory.objects.all()
        self.assertEqual(all_transitions.count(), 1)

        from_entries = UserEntryTransitionHistory.objects.filter(entry_from=https_entry)
        self.assertEqual(from_entries.count(), 1)

        visits = UserEntryVisitHistory.objects.all()
        self.assertEqual(visits.count(), 2)

        visits = UserEntryVisitHistory.objects.filter(entry=https_entry)
        self.assertEqual(visits.count(), 1)

    def test_move_entry_to_url__destination_exists(self):
        https_entry = LinkDataController.objects.create(
            source_url="https://archive.com/test",
            link="https://testlink.com",
            title="The archive https link",
            bookmarked=True,
            language="en",
            date_published=DateUtils.get_datetime_now_utc() - timedelta(days=3),
        )

        http_entry = LinkDataController.objects.create(
            source_url="http://archive.com/test",
            link="http://testlink.com",
            title="The archive https link",
            bookmarked=True,
            language="en",
            date_published=DateUtils.get_datetime_now_utc() - timedelta(days=3),
        )

        youtube_entry = LinkDataController.objects.create(
            source_url="http://youtube.com/test",
            link="http://youtube.com?v=1",
            title="The archive https link",
            bookmarked=True,
            language="en",
            date_published=DateUtils.get_datetime_now_utc() - timedelta(days=3),
        )

        UserTags.set_tag(http_entry, "test", self.user_not_staff)
        UserVotes.add(self.user_not_staff, http_entry, 30)
        UserComments.add(self.user_not_staff, http_entry, "This is stupid")
        UserBookmarks.add(self.user_not_staff, http_entry)

        # UserEntryTransitionHistory.add(self.user_not_staff, entry_from = http_entry, entry_to = youtube_entry)
        # UserEntryTransitionHistory.add(self.user_not_staff, entry_from = youtube_entry, entry_to = http_entry)

        UserEntryVisitHistory.visited(http_entry, self.user_not_staff)
        UserEntryVisitHistory.visited(youtube_entry, self.user_not_staff)

        # verify before call

        tags = UserTags.objects.all()
        self.assertEqual(tags.count(), 1)

        all_transitions = UserEntryTransitionHistory.objects.all()
        self.assertEqual(all_transitions.count(), 1)
        transition = all_transitions[0]
        self.assertEqual(transition.entry_from, http_entry)
        self.assertEqual(transition.entry_to, youtube_entry)

        # call tested function
        result = EntryWrapper(entry=http_entry).move_entry_to_url(https_entry.link)

        # Check expected behavior

        self.print_errors()

        https_entries = LinkDataController.objects.filter(link="https://testlink.com")
        http_entries = LinkDataController.objects.filter(link="http://testlink.com")

        self.assertEqual(https_entries.count(), 1)
        self.assertEqual(http_entries.count(), 0)

        tags = UserTags.objects.all()
        self.assertEqual(tags.count(), 1)
        tag = tags[0]
        self.assertEqual(tag.entry, https_entry)

        votes = UserVotes.objects.all()
        self.assertEqual(votes.count(), 1)
        vote = votes[0]
        self.assertEqual(vote.entry, https_entry)

        comments = UserComments.objects.all()
        self.assertEqual(comments.count(), 1)
        comment = comments[0]
        self.assertEqual(comment.entry, https_entry)

        bookmarks = UserBookmarks.objects.all()
        self.assertEqual(bookmarks.count(), 1)
        bookmark = bookmarks[0]
        self.assertEqual(bookmark.entry, https_entry)

        all_transitions = UserEntryTransitionHistory.objects.all()
        self.assertEqual(all_transitions.count(), 1)

        from_entries = UserEntryTransitionHistory.objects.filter(entry_from=https_entry)
        self.assertEqual(from_entries.count(), 1)

        visits = UserEntryVisitHistory.objects.all()
        self.assertEqual(visits.count(), 2)

        visits = UserEntryVisitHistory.objects.filter(entry=https_entry)
        self.assertEqual(visits.count(), 1)

    def test_move_entry_to_url__destination_does_not_exist(self):
        http_entry = LinkDataController.objects.create(
            source_url="http://archive.com/test",
            link="http://testlink.com",
            title="The archive https link",
            bookmarked=True,
            language="en",
            date_published=DateUtils.get_datetime_now_utc() - timedelta(days=3),
        )

        youtube_entry = LinkDataController.objects.create(
            source_url="http://youtube.com/test",
            link="http://youtube.com?v=1",
            title="The archive https link",
            bookmarked=True,
            language="en",
            date_published=DateUtils.get_datetime_now_utc() - timedelta(days=3),
        )

        UserTags.set_tag(http_entry, "test", self.user_not_staff)
        UserVotes.add(self.user_not_staff, http_entry, 30)
        UserComments.add(self.user_not_staff, http_entry, "This is stupid")
        UserBookmarks.add(self.user_not_staff, http_entry)

        # UserEntryTransitionHistory.add(self.user_not_staff, entry_from = http_entry, entry_to = youtube_entry)
        # UserEntryTransitionHistory.add(self.user_not_staff, entry_from = youtube_entry, entry_to = http_entry)

        UserEntryVisitHistory.visited(http_entry, self.user_not_staff)
        UserEntryVisitHistory.visited(youtube_entry, self.user_not_staff)

        # verify before call

        tags = UserTags.objects.all()
        self.assertEqual(tags.count(), 1)

        all_transitions = UserEntryTransitionHistory.objects.all()
        self.assertEqual(all_transitions.count(), 1)
        transition = all_transitions[0]
        self.assertEqual(transition.entry_from, http_entry)
        self.assertEqual(transition.entry_to, youtube_entry)

        # call tested function
        result = EntryWrapper(entry=http_entry).move_entry_to_url(
            http_entry.get_https_url()
        )

        # Check expected behavior

        self.print_errors()

        https_entries = LinkDataController.objects.filter(link="https://testlink.com")
        http_entries = LinkDataController.objects.filter(link="http://testlink.com")

        self.assertEqual(https_entries.count(), 1)
        self.assertEqual(http_entries.count(), 0)

        # http_entry object has been changed to have https:// link inside

        tags = UserTags.objects.all()
        self.assertEqual(tags.count(), 1)
        tag = tags[0]
        self.assertEqual(tag.entry, http_entry)

        votes = UserVotes.objects.all()
        self.assertEqual(votes.count(), 1)
        vote = votes[0]
        self.assertEqual(vote.entry, http_entry)

        comments = UserComments.objects.all()
        self.assertEqual(comments.count(), 1)
        comment = comments[0]
        self.assertEqual(comment.entry, http_entry)

        bookmarks = UserBookmarks.objects.all()
        self.assertEqual(bookmarks.count(), 1)
        bookmark = bookmarks[0]
        self.assertEqual(bookmark.entry, http_entry)

        all_transitions = UserEntryTransitionHistory.objects.all()
        self.assertEqual(all_transitions.count(), 1)

        from_entries = UserEntryTransitionHistory.objects.filter(entry_from=http_entry)
        self.assertEqual(from_entries.count(), 1)

        visits = UserEntryVisitHistory.objects.all()
        self.assertEqual(visits.count(), 2)

        visits = UserEntryVisitHistory.objects.filter(entry=http_entry)
        self.assertEqual(visits.count(), 1)
