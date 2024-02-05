from django.test import TestCase

from ..models import UserSearchHistory, UserEntryTransitionHistory
from ..controllers import LinkDataController
from ..configuration import Configuration


class UserSearchHistoryTest(TestCase):

    def setUp(self):
        c = Configuration.get_object()
        c.config_entry.track_user_actions = True
        c.config_entry.track_user_searches = True
        c.config_entry.track_user_navigation = True
        c.config_entry.save()

        LinkDataController.objects.create(
          link = "https://youtube.com",
          description = "",
          title = "",
        )

        LinkDataController.objects.create(
          link = "https://tiktok.com",
          description = "",
          title = "",
        )

        LinkDataController.objects.create(
          link = "https://odysee.com",
          description = "",
          title = "",
        )

        LinkDataController.objects.create(
          link = "https://spotify.com",
          description = "",
          title = "",
        )

    def test_add(self):
        # call tested function
        theobject = UserSearchHistory.add("test_user1", "query1")

        objects = UserSearchHistory.objects.all()

        self.assertEqual(objects.count(), 1)
        self.assertEqual(objects[0], theobject)

    def test_more_than_limit(self):
        for index in range(1, 102):
            user = "test_user{}".format(index)
            query = "query{}".format(index)
            #print("User:{} Query:{}".format(user, query))

            # call tested function
            UserSearchHistory.add(user, query)

        objects = UserSearchHistory.objects.all()

        self.assertEqual(objects.count(), UserSearchHistory.get_choices_model_limit())


class UserEntryTransitionHistoryTest(TestCase):

    def setUp(self):
        c = Configuration.get_object()
        c.config_entry.track_user_actions = True
        c.config_entry.track_user_searches = True
        c.config_entry.track_user_navigation = True
        c.config_entry.save()

        self.entry_youtube = LinkDataController.objects.create(
          link = "https://youtube.com",
          description = "",
          title = "",
        )

        self.entry_tiktok = LinkDataController.objects.create(
          link = "https://tiktok.com",
          description = "",
          title = "",
        )

        self.entry_odysee = LinkDataController.objects.create(
          link = "https://odysee.com",
          description = "",
          title = "",
        )

        self.entry_spotify = LinkDataController.objects.create(
          link = "https://spotify.com",
          description = "",
          title = "",
        )

    def test_add_or_increment(self):
        UserEntryTransitionHistory.objects.all().delete()

        # cal tested function
        entry1 = UserEntryTransitionHistory.add("test_user",
                                                        self.entry_youtube,
                                                        self.entry_tiktok)

        self.assertTrue(entry1)
        self.assertEqual(entry1.user, "test_user")
        self.assertEqual(entry1.entry_from.id, self.entry_youtube.id)
        self.assertEqual(entry1.entry_to.id, self.entry_tiktok.id)

    def test_add_to_same(self):
        UserEntryTransitionHistory.objects.all().delete()

        # cal tested function
        entry = UserEntryTransitionHistory.add("test_user",
                                                        self.entry_youtube,
                                                        self.entry_youtube)

        self.assertTrue(not entry)

    def test_add_or_increment_none(self):
        UserEntryTransitionHistory.objects.all().delete()

        # cal tested function
        entry1 = UserEntryTransitionHistory.add("test_user",
                                                        None,
                                                        self.entry_tiktok)

        self.assertTrue(entry1)
        self.assertEqual(entry1.user, "test_user")
        self.assertEqual(entry1.entry_from, None)
        self.assertEqual(entry1.entry_to.id, self.entry_tiktok.id)

    def test_add_or_increment_two(self):

        # call tested function
        entry1 = UserEntryTransitionHistory.add("test_user",
                                                        self.entry_youtube,
                                                        self.entry_tiktok)

        # call tested function
        entry2 = UserEntryTransitionHistory.add("test_user",
                                                        self.entry_tiktok,
                                                        self.entry_youtube)

        self.assertTrue(entry2)
        self.assertEqual(entry2.user, "test_user")
        self.assertEqual(entry2.entry_from.id, self.entry_tiktok.id)
        self.assertEqual(entry2.entry_to.id, self.entry_youtube.id)

    def test_get_related_list(self):

        UserEntryTransitionHistory.add("test_user",
                                                        self.entry_youtube,
                                                        self.entry_tiktok)

        UserEntryTransitionHistory.add("test_user",
                                                        self.entry_youtube,
                                                        self.entry_odysee)

        UserEntryTransitionHistory.add("test_user",
                                                        self.entry_tiktok,
                                                        self.entry_spotify)

        # call tested function
        related_list = UserEntryTransitionHistory.get_related_list("test_user", self.entry_youtube)

        self.assertEqual(len(related_list), 2)
        self.assertEqual(related_list[0].id, self.entry_tiktok.id)
        self.assertEqual(related_list[1].id, self.entry_odysee.id)
