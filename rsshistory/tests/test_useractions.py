from django.contrib.auth.models import User
from datetime import timedelta
from django.test import TestCase

from ..controllers import LinkDataController, SourceDataController, DomainsController
from ..configuration import Configuration
from ..models import (
    UserTags,
    UserVotes,
    UserBookmarks,
    CompactedTags,
    UserCompactedTags,
)
from utils.dateutils import DateUtils


class UserTagsTest(TestCase):
    def setUp(self):
        c = Configuration.get_object()

        current_time = DateUtils.get_datetime_now_utc()
        domain = DomainsController.objects.create(
            domain="https://youtube.com",
        )

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            export_to_cms=True,
            remove_after_days=1,
        )

        self.entry = LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=bookmarked",
            title="The first link",
            source=source_youtube,
            bookmarked=True,
            language="en",
            domain=domain,
            date_published=current_time,
        )

        self.entry_new = LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="http://youtube.com?v=bookmarked",
            title="The first link",
            source=source_youtube,
            bookmarked=True,
            language="en",
            domain=domain,
            date_published=current_time,
        )

        self.user = User.objects.create_user(
            username="test_username", password="testpassword"
        )

        self.user_super = User.objects.create_user(
            username="test_username2",
            password="testpassword",
            is_superuser=True,
        )

    def test_set_tags(self):
        UserTags.objects.all().delete()

        data = {}
        data["tag"] = "tag1, tag2"

        # call tested function
        UserTags.set_tags(self.entry, data["tag"], self.user)

        tags = UserTags.objects.all()

        tag_names = [tag.tag for tag in tags]

        self.assertEqual(tags.count(), 2)
        self.assertTrue("tag1" in tag_names)
        self.assertTrue("tag2" in tag_names)
        self.assertEqual(tags[0].entry, self.entry)
        self.assertEqual(tags[1].entry, self.entry)

    def test_set_tags_map(self):
        UserTags.objects.all().delete()

        data = {}
        data["user"] = self.user
        data["tags"] = ["tag1", "tag2"]
        data["entry"] = self.entry

        # call tested function
        UserTags.set_tags_map(data)

        tags = UserTags.objects.all()

        self.assertEqual(tags.count(), 2)

        self.assertEqual(tags[0].entry, self.entry)
        self.assertEqual(tags[1].entry, self.entry)

        tag_values = UserTags.objects.all().values_list("tag", flat=True)
        self.assertTrue("tag1" in tag_values)
        self.assertTrue("tag2" in tag_values)

    def test_set_tag(self):
        UserTags.objects.all().delete()

        user = self.user

        # call tested function
        UserTags.set_tag(self.entry, "tag3", user)
        # call tested function
        UserTags.set_tag(self.entry, "tag4", user)

        tags = UserTags.objects.all()
        tag_values = UserTags.objects.all().values_list("tag", flat=True)

        self.assertEqual(tags.count(), 2)
        self.assertEqual(tags[0].entry, self.entry)
        self.assertEqual(tags[1].entry, self.entry)

        self.assertTrue("tag3" in tag_values)
        self.assertTrue("tag4" in tag_values)

    def test_cleanup(self):
        user = self.user

        UserTags.objects.create(user=None, entry=self.entry, tag="test")

        # call tested function
        UserTags.cleanup({"verify": True})

        tags = UserTags.objects.all()

        self.assertEqual(tags.count(), 0)

    def test_move_entry(self):
        user = self.user

        UserTags.set_tag(self.entry, "tag3", user)
        # call tested function
        UserTags.move_entry(self.entry, self.entry_new)

        tags = UserTags.objects.all()

        self.assertEqual(tags.count(), 1)
        self.assertEqual(tags[0].entry, self.entry_new)
        self.assertEqual(tags[0].user, self.user)


class UserCompactedTagsTest(TestCase):
    def setUp(self):
        c = Configuration.get_object()

        current_time = DateUtils.get_datetime_now_utc()
        domain = DomainsController.objects.create(
            domain="https://youtube.com",
        )

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            export_to_cms=True,
            remove_after_days=1,
        )

        self.entry1 = LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=bookmarked",
            title="The first link",
            source=source_youtube,
            bookmarked=True,
            language="en",
            domain=domain,
            date_published=current_time,
        )
        self.entry2 = LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=bookmarked2",
            title="The first link",
            source=source_youtube,
            bookmarked=True,
            language="en",
            domain=domain,
            date_published=current_time,
        )

        self.user = User.objects.create_user(
            username="test_username", password="testpassword"
        )

        self.user_super = User.objects.create_user(
            username="test_username2",
            password="testpassword",
            is_superuser=True,
        )

    def test_set_tags__compacts(self):
        UserTags.objects.all().delete()
        UserCompactedTags.objects.all().delete()

        data = {}
        data["tag"] = "tag1, tag2"

        # call tested function
        UserTags.set_tags(self.entry1, data["tag"], self.user)
        # call tested function
        UserTags.set_tags(self.entry2, data["tag"], self.user)

        compacts = UserCompactedTags.objects.all()
        self.assertEqual(compacts.count(), 2)

        self.assertEqual(compacts[0].count, 2)
        self.assertEqual(compacts[1].count, 2)

        compact_list = compacts.values_list("tag", flat=True)
        self.assertTrue("tag1" in compact_list)
        self.assertTrue("tag2" in compact_list)


class CompactedTagsTest(TestCase):
    def setUp(self):
        c = Configuration.get_object()

        current_time = DateUtils.get_datetime_now_utc()
        domain = DomainsController.objects.create(
            domain="https://youtube.com",
        )

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            export_to_cms=True,
            remove_after_days=1,
        )

        self.entry = LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=bookmarked",
            title="The first link",
            source=source_youtube,
            bookmarked=True,
            language="en",
            domain=domain,
            date_published=current_time,
        )

        self.user = User.objects.create_user(
            username="test_username", password="testpassword"
        )

        self.user_super = User.objects.create_user(
            username="test_username2",
            password="testpassword",
            is_superuser=True,
        )

    def test_set_tags__compacts(self):
        UserTags.objects.all().delete()

        data = {}
        data["tag"] = "tag1, tag2"

        # call tested function
        UserTags.set_tags(self.entry, data["tag"], self.user)

        compacts = CompactedTags.objects.all()
        self.assertEqual(compacts.count(), 2)

        self.assertEqual(compacts[0].count, 1)
        self.assertEqual(compacts[1].count, 1)

        compact_list = compacts.values_list("tag", flat=True)
        self.assertTrue("tag1" in compact_list)
        self.assertTrue("tag2" in compact_list)

        data["tag"] = "tag1, tag2"
        # call tested function
        UserTags.set_tags(self.entry, data["tag"], self.user_super)

        compacts = CompactedTags.objects.all()
        self.assertEqual(compacts.count(), 2)

        self.assertEqual(compacts[0].count, 2)
        self.assertEqual(compacts[1].count, 2)

        compact_list = compacts.values_list("tag", flat=True)
        self.assertTrue("tag1" in compact_list)
        self.assertTrue("tag2" in compact_list)


class UserVotesTest(TestCase):
    def setUp(self):
        c = Configuration.get_object()

        self.entry = None
        self.user = None

    def create_entry(self):
        current_time = DateUtils.get_datetime_now_utc()

        if not self.entry:
            self.entry = LinkDataController.objects.create(
                source_url="https://youtube.com",
                link="https://youtube.com?v=bookmarked",
                title="The first link",
                source=None,
                bookmarked=True,
                language="en",
                domain=None,
                date_published=current_time,
            )
            self.entry_new = LinkDataController.objects.create(
                source_url="https://youtube.com",
                link="http://youtube.com?v=bookmarked",
                title="The first link",
                source=None,
                bookmarked=True,
                language="en",
                domain=None,
                date_published=current_time,
            )

        if not self.user:
            self.user = User.objects.create_user(
                username="test_username", password="testpassword"
            )
            self.user_super = User.objects.create_user(
                username="test_username2", password="testpassword", is_superuser=True
            )

    def test_add__nonzero(self):
        self.create_entry()

        UserVotes.objects.all().delete()

        # call tested function
        UserVotes.add(self.user, self.entry, 50)

        votes = UserVotes.objects.all()
        self.assertEqual(votes.count(), 1)
        self.assertEqual(votes[0].vote, 50)
        self.assertEqual(votes[0].entry, self.entry)

    def test_add__zero(self):
        self.create_entry()

        UserVotes.objects.all().delete()

        # call tested function
        UserVotes.add(self.user, self.entry, 0)

        votes = UserVotes.objects.all()
        self.assertEqual(votes.count(), 0)

    def test_get_user_vote(self):
        self.create_entry()

        UserVotes.objects.all().delete()

        vote = UserVotes.objects.create(
            user=self.user,
            entry=self.entry,
            vote=20,
        )

        # call tested function
        vote = UserVotes.get_user_vote(self.user, self.entry)

        self.assertEqual(vote, 20)

    def test_cleanup(self):
        self.create_entry()

        self.entry.page_rating_votes = 10
        self.entry.save()

        # call tested function
        UserVotes.cleanup({"verify": True})

        entries = LinkDataController.objects.all()
        self.assertTrue(entries.count(), 1)

    def test_move_entry(self):
        self.create_entry()

        UserVotes.objects.all().delete()

        UserVotes.add(self.user, self.entry, 50)

        # call tested function
        UserVotes.move_entry(self.entry, self.entry_new)

        votes = UserVotes.objects.all()
        self.assertEqual(votes.count(), 1)
        self.assertEqual(votes[0].vote, 50)
        self.assertEqual(votes[0].entry, self.entry_new)


class UserBookmarksTest(TestCase):
    def setUp(self):
        c = Configuration.get_object()

        self.entry = None
        self.user = None

    def create_entry(self):
        current_time = DateUtils.get_datetime_now_utc()

        if not self.entry:
            self.entry = LinkDataController.objects.create(
                source_url="https://youtube.com",
                link="https://youtube.com?v=bookmarked",
                title="The first link",
                source=None,
                bookmarked=True,
                language="en",
                domain=None,
                date_published=current_time,
            )
            self.entry_new = LinkDataController.objects.create(
                source_url="https://youtube.com",
                link="http://youtube.com?v=bookmarked",
                title="The first link",
                source=None,
                bookmarked=True,
                language="en",
                domain=None,
                date_published=current_time,
            )

        if not self.user:
            self.user = User.objects.create_user(
                username="test_username", password="testpassword"
            )
            self.user_super = User.objects.create_user(
                username="test_username2", password="testpassword", is_superuser=True
            )

    def test_add(self):
        UserBookmarks.objects.all().delete()

        self.create_entry()

        self.entry.bookmarked = False
        self.entry.save()

        # call tested function
        UserBookmarks.add(self.user, self.entry)

        bookmarks = UserBookmarks.objects.all()
        self.assertTrue(bookmarks.count(), 1)
        self.assertEqual(bookmarks[0].entry, self.entry)

    def test_remove(self):
        UserBookmarks.objects.all().delete()

        self.create_entry()

        UserBookmarks.add(self.user, self.entry)
        bookmarks = UserBookmarks.objects.all()
        self.assertTrue(bookmarks.count(), 1)
        self.assertEqual(bookmarks[0].entry, self.entry)

        # call tested function
        UserBookmarks.remove(self.user, self.entry)
        bookmarks = UserBookmarks.objects.all()
        self.assertEqual(bookmarks.count(), 0)

    def test_move_entry(self):
        UserBookmarks.objects.all().delete()

        self.create_entry()

        UserBookmarks.add(self.user, self.entry)

        # call tested function
        UserBookmarks.move_entry(self.entry, self.entry_new)

        bookmarks = UserBookmarks.objects.all()
        self.assertTrue(bookmarks.count(), 1)
        self.assertEqual(bookmarks[0].entry, self.entry_new)

    def test_cleanup(self):
        UserBookmarks.objects.all().delete()

        self.create_entry()

        self.entry.bookmarked = True
        self.entry.save()

        # call tested function
        UserBookmarks.cleanup({"verify": True})

        self.entry.refresh_from_db()
        self.assertTrue(self.entry.bookmarked, False)
