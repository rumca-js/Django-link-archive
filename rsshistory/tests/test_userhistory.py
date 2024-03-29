from datetime import timedelta
from django.test import TestCase
from django.contrib.auth.models import User

from .fakeinternet import FakeInternetTestCase

from ..models import UserEntryVisitHistory
from ..models import UserSearchHistory, UserEntryTransitionHistory
from ..controllers import LinkDataController, SourceDataController
from ..dateutils import DateUtils
from ..configuration import Configuration


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

    def test_add_or_increment(self):
        UserEntryTransitionHistory.objects.all().delete()

        # cal tested function
        entry1 = UserEntryTransitionHistory.add(
            self.user, self.entry_youtube, self.entry_tiktok
        )

        self.assertTrue(entry1)
        self.assertEqual(entry1.user_object, self.user)
        self.assertEqual(entry1.entry_from.id, self.entry_youtube.id)
        self.assertEqual(entry1.entry_to.id, self.entry_tiktok.id)

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
        self.assertEqual(entry1.user_object, self.user)
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
        self.assertEqual(entry2.user_object, self.user)
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
            url="https://youtube.com", title="YouTube", category="No", subcategory="No"
        )

        self.youtube_object = LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=12345",
            source_obj=ob,
        )

        self.tiktok_object = LinkDataController.objects.create(
            source="https://tiktok.com",
            link="https://tiktok.com?v=12345",
            source_obj=ob,
        )

        self.odysee_object = LinkDataController.objects.create(
            source="https://odysee.com",
            link="https://odysee.com?v=12345",
            source_obj=ob,
        )

        self.user = User.objects.create_user(
            username="test_username", password="testpassword"
        )

    def test_entry_visit_two_visits(self):
        entries = LinkDataController.objects.filter(link="https://youtube.com?v=12345")

        self.assertEqual(entries.count(), 1)

        # call tested function
        UserEntryVisitHistory.visited(entries[0], self.user)

        visits = UserEntryVisitHistory.objects.filter(entry_object=entries[0])
        self.assertEqual(visits.count(), 1)
        self.assertEqual(visits[0].visits, 1)
        self.assertEqual(visits[0].user_object, self.user)

        # call tested function
        UserEntryVisitHistory.visited(entries[0], self.user)

        # this call is not taken into consideration. Happened to fast. refresh, etc.

        visits = UserEntryVisitHistory.objects.filter(entry_object=entries[0])
        self.assertEqual(visits.count(), 1)
        self.assertEqual(visits[0].visits, 1)
        self.assertEqual(visits[0].user_object, self.user)

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
            entry_object=self.youtube_object,
            user_object=self.user,
        )
        UserEntryVisitHistory.objects.create(
            visits=2,
            date_last_visit=date_2,
            entry_object=self.tiktok_object,
            user_object=self.user,
        )
        UserEntryVisitHistory.objects.create(
            visits=2,
            date_last_visit=date_3,
            entry_object=self.odysee_object,
            user_object=self.user,
        )

        # call tested function
        entry = UserEntryVisitHistory.get_last_user_entry(self.user)

        self.assertTrue(entry)
        self.assertEqual(entry, self.tiktok_object)

    def test_entry_get_last_user_entry_not_found(self):
        UserEntryVisitHistory.objects.create(
            user_object=self.user,
            visits=2,
            date_last_visit=DateUtils.get_datetime_now_utc() - timedelta(hours=2),
            entry_object=self.youtube_object,
        )

        # call tested function
        entry = UserEntryVisitHistory.get_last_user_entry(self.user)

        self.assertFalse(entry)
