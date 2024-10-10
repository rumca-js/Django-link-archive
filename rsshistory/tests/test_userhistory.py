from datetime import timedelta
from django.test import TestCase
from django.contrib.auth.models import User

from utils.dateutils import DateUtils

from ..models import (
    UserEntryVisitHistory,
    UserSearchHistory,
    UserEntryTransitionHistory,
)
from ..controllers import LinkDataController, SourceDataController
from ..configuration import Configuration
from .fakeinternet import FakeInternetTestCase


class UserSearchHistoryTest(TestCase):
    def setUp(self):
        c = Configuration.get_object()
        c.config_entry.track_user_actions = True
        c.config_entry.track_user_searches = True
        c.config_entry.track_user_navigation = True
        c.config_entry.save()

        LinkDataController.objects.create(
            link="https://youtube.com",
            description="",
            title="",
        )

        LinkDataController.objects.create(
            link="https://tiktok.com",
            description="",
            title="",
        )

        LinkDataController.objects.create(
            link="https://odysee.com",
            description="",
            title="",
        )

        LinkDataController.objects.create(
            link="https://spotify.com",
            description="",
            title="",
        )

        self.user = User.objects.create_user(
            username="test_username", password="testpassword"
        )

    def test_add(self):
        # call tested function
        theobject = UserSearchHistory.add(self.user, "query1")

        objects = UserSearchHistory.objects.all()

        self.assertEqual(objects.count(), 1)
        self.assertEqual(objects[0], theobject)

    def test_add__operator(self):
        # call tested function
        theobject = UserSearchHistory.add(self.user, "title = test & description = multiple")

        objects = UserSearchHistory.objects.all()

        self.assertEqual(objects.count(), 1)
        self.assertEqual(objects[0], theobject)
        self.assertEqual(theobject.search_query, "title = test & description = multiple")

    def test_get_encoded_search_query(self):
        # call tested function
        theobject = UserSearchHistory.add(self.user, "title = test & description = multiple")

        self.assertEqual(theobject.get_encoded_search_query(), "title%20%3D%20test%20%26%20description%20%3D%20multiple")

    def test_more_than_limit(self):
        limit = UserSearchHistory.get_choices_model_limit()

        for index in range(1, limit + 20):
            user = "test_user{}".format(index)
            query = "query{}".format(index)
            # print("User:{} Query:{}".format(user, query))

            # call tested function
            UserSearchHistory.add(self.user, query)

        objects = UserSearchHistory.objects.all()

        self.assertEqual(objects.count(), limit)


class UserEntryTransitionHistoryTest(TestCase):
    def setUp(self):
        c = Configuration.get_object()
        c.config_entry.track_user_actions = True
        c.config_entry.track_user_searches = True
        c.config_entry.track_user_navigation = True
        c.config_entry.save()

        self.entry_youtube = LinkDataController.objects.create(
            link="https://youtube.com",
            description="",
            title="",
        )

        self.entry_tiktok = LinkDataController.objects.create(
            link="https://tiktok.com",
            description="",
            title="",
        )

        self.entry_odysee = LinkDataController.objects.create(
            link="https://odysee.com",
            description="",
            title="",
        )

        self.entry_spotify = LinkDataController.objects.create(
            link="https://spotify.com",
            description="",
            title="",
        )

        self.user = User.objects.create_user(
            username="test_username", password="testpassword"
        )

        self.entry_youtube_new = LinkDataController.objects.create(
            link="http://youtube.com",
            description="",
            title="",
        )

    def test_add_or_increment(self):
        UserEntryTransitionHistory.objects.all().delete()

        # cal tested function
        entry1 = UserEntryTransitionHistory.add(
            self.user, self.entry_youtube, self.entry_tiktok
        )

        self.assertTrue(entry1)
        self.assertEqual(entry1.user, self.user)
        self.assertEqual(entry1.entry_from.id, self.entry_youtube.id)
        self.assertEqual(entry1.entry_to.id, self.entry_tiktok.id)

    def test_move_entry__from(self):
        UserEntryTransitionHistory.objects.all().delete()

        entry1 = UserEntryTransitionHistory.add(
            self.user, self.entry_youtube, self.entry_tiktok
        )

        # cal tested function
        UserEntryTransitionHistory.move_entry(
            self.entry_youtube, self.entry_youtube_new
        )

        transitions = UserEntryTransitionHistory.objects.all()
        self.assertTrue(transitions.count() > 0)
        self.assertTrue(transitions[0].entry_from, self.entry_youtube_new)

    def test_move_entry__to(self):
        UserEntryTransitionHistory.objects.all().delete()

        entry1 = UserEntryTransitionHistory.add(
            self.user, self.entry_tiktok, self.entry_youtube
        )

        # cal tested function
        UserEntryTransitionHistory.move_entry(
            self.entry_youtube, self.entry_youtube_new
        )

        transitions = UserEntryTransitionHistory.objects.all()
        self.assertTrue(transitions.count() > 0)
        self.assertTrue(transitions[0].entry_to, self.entry_youtube_new)

    def test_add_to_same(self):
        UserEntryTransitionHistory.objects.all().delete()

        # cal tested function
        entry = UserEntryTransitionHistory.add(
            self.user, self.entry_youtube, self.entry_youtube
        )

        self.assertTrue(not entry)

    def test_add_or_increment_none(self):
        UserEntryTransitionHistory.objects.all().delete()

        # cal tested function
        entry1 = UserEntryTransitionHistory.add(self.user, None, self.entry_tiktok)

        self.assertTrue(entry1)
        self.assertEqual(entry1.user, self.user)
        self.assertEqual(entry1.entry_from, None)
        self.assertEqual(entry1.entry_to.id, self.entry_tiktok.id)

    def test_add_or_increment_two(self):
        # call tested function
        entry1 = UserEntryTransitionHistory.add(
            self.user, self.entry_youtube, self.entry_tiktok
        )

        # call tested function
        entry2 = UserEntryTransitionHistory.add(
            self.user, self.entry_tiktok, self.entry_youtube
        )

        self.assertTrue(entry2)
        self.assertEqual(entry2.user, self.user)
        self.assertEqual(entry2.entry_from.id, self.entry_tiktok.id)
        self.assertEqual(entry2.entry_to.id, self.entry_youtube.id)

    def test_get_related_list(self):
        UserEntryTransitionHistory.add(self.user, self.entry_youtube, self.entry_tiktok)

        UserEntryTransitionHistory.add(self.user, self.entry_youtube, self.entry_odysee)

        UserEntryTransitionHistory.add(self.user, self.entry_tiktok, self.entry_spotify)

        # call tested function
        related_list = UserEntryTransitionHistory.get_related_list(
            self.user, self.entry_youtube
        )

        self.assertEqual(len(related_list), 2)
        self.assertEqual(related_list[0].id, self.entry_tiktok.id)
        self.assertEqual(related_list[1].id, self.entry_odysee.id)


class UserEntryVisitHistoryTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        c = Configuration.get_object().config_entry
        c.track_user_actions = True
        c.track_user_navigation = True
        c.save()

        ob = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
        )

        self.youtube_object = LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=12345",
            source=ob,
        )

        self.tiktok_object = LinkDataController.objects.create(
            source_url="https://tiktok.com",
            link="https://tiktok.com?v=12345",
            source=ob,
        )

        self.odysee_object = LinkDataController.objects.create(
            source_url="https://odysee.com",
            link="https://odysee.com?v=12345",
            source=ob,
        )

        self.youtube_object_new = LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="http://youtube.com?v=12345",
            source=ob,
        )

        self.user = User.objects.create_user(
            username="test_username", password="testpassword"
        )

    def test_visited__two_times_same(self):
        entries = LinkDataController.objects.filter(link="https://youtube.com?v=12345")

        self.assertEqual(entries.count(), 1)

        # call tested function
        UserEntryVisitHistory.visited(entries[0], self.user)

        visits = UserEntryVisitHistory.objects.filter(entry=entries[0])
        self.assertEqual(visits.count(), 1)
        self.assertEqual(visits[0].visits, 1)
        self.assertEqual(visits[0].user, self.user)

        # call tested function
        UserEntryVisitHistory.visited(entries[0], self.user)

        # this call is not taken into consideration. Happened to fast. refresh, etc.

        visits = UserEntryVisitHistory.objects.filter(entry=entries[0])
        self.assertEqual(visits.count(), 1)
        self.assertEqual(visits[0].visits, 1)
        self.assertEqual(visits[0].user, self.user)

    def test_visited__argument_transition_from(self):
        youtube_entries = LinkDataController.objects.filter(
            link="https://youtube.com?v=12345"
        )
        tiktok_entries = LinkDataController.objects.filter(
            link="https://tiktok.com?v=12345"
        )

        self.assertEqual(youtube_entries.count(), 1)
        self.assertEqual(tiktok_entries.count(), 1)

        # call tested function
        UserEntryVisitHistory.visited(youtube_entries[0], self.user, tiktok_entries[0])

        visits = UserEntryVisitHistory.objects.filter(entry=youtube_entries[0])
        self.assertEqual(visits.count(), 1)
        self.assertEqual(visits[0].visits, 1)
        self.assertEqual(visits[0].user, self.user)

        all_transitions = UserEntryTransitionHistory.objects.all()
        self.assertEqual(all_transitions.count(), 1)
        transition = all_transitions[0]
        self.assertEqual(transition.entry_from, tiktok_entries[0])
        self.assertEqual(transition.entry_to, youtube_entries[0])

    def test_entry_get_last_user_entry(self):
        """
        item cannot be too old, and cannot be too new
        """
        date_1 = DateUtils.get_datetime_now_utc() - timedelta(days=2)
        date_2 = DateUtils.get_datetime_now_utc() - timedelta(minutes=2)
        date_3 = DateUtils.get_datetime_now_utc() - timedelta(seconds=2)

        UserEntryVisitHistory.objects.create(
            visits=2,
            date_last_visit=date_1,
            entry=self.youtube_object,
            user=self.user,
        )
        UserEntryVisitHistory.objects.create(
            visits=2,
            date_last_visit=date_2,
            entry=self.tiktok_object,
            user=self.user,
        )
        UserEntryVisitHistory.objects.create(
            visits=2,
            date_last_visit=date_3,
            entry=self.odysee_object,
            user=self.user,
        )

        # call tested function
        entry = UserEntryVisitHistory.get_last_user_entry(self.user)

        self.assertTrue(entry)
        self.assertEqual(entry, self.tiktok_object)

    def test_entry_get_last_user_entry_not_found(self):
        UserEntryVisitHistory.objects.create(
            user=self.user,
            visits=2,
            date_last_visit=DateUtils.get_datetime_now_utc() - timedelta(hours=2),
            entry=self.youtube_object,
        )

        # call tested function
        entry = UserEntryVisitHistory.get_last_user_entry(self.user)

        self.assertFalse(entry)

    def test_move_entry(self):
        UserEntryVisitHistory.visited(self.youtube_object, self.user)

        # call tested function
        UserEntryVisitHistory.move_entry(self.youtube_object, self.youtube_object_new)

        rows = UserEntryVisitHistory.objects.filter(entry=self.youtube_object_new)

        self.assertTrue(rows.count() > 0)
        self.assertEqual(rows[0].entry, self.youtube_object_new)

    def test_visit_burst(self):
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

        UserEntryVisitHistory.visited(http_entry, self.user)
        UserEntryVisitHistory.visited(youtube_entry, self.user)

        # verify before call

        all_transitions = UserEntryTransitionHistory.objects.all()
        self.assertEqual(all_transitions.count(), 1)
        transition = all_transitions[0]
        self.assertEqual(transition.entry_from, http_entry)
        self.assertEqual(transition.entry_to, youtube_entry)
