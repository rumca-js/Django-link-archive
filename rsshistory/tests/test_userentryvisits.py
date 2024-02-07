from datetime import timedelta

from ..models import UserEntryVisits
from ..controllers import LinkDataController, SourceDataController
from ..dateutils import DateUtils
from ..configuration import Configuration

from .fakeinternet import FakeInternetTestCase


class UserEntryVisitsTest(FakeInternetTestCase):
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

    def test_entry_visit_two_visits(self):
        entries = LinkDataController.objects.filter(link="https://youtube.com?v=12345")

        self.assertEqual(entries.count(), 1)

        # call tested function
        UserEntryVisits.visited(entries[0], "test_username")

        visits = UserEntryVisits.objects.filter(entry_object=entries[0])
        self.assertEqual(visits.count(), 1)
        self.assertEqual(visits[0].visits, 1)
        self.assertEqual(visits[0].user, "test_username")

        # call tested function
        UserEntryVisits.visited(entries[0], "test_username")

        # this call is not taken into consideration. Happened to fast. refresh, etc.

        visits = UserEntryVisits.objects.filter(entry_object=entries[0])
        self.assertEqual(visits.count(), 1)
        self.assertEqual(visits[0].visits, 1)
        self.assertEqual(visits[0].user, "test_username")

    def test_entry_get_last_user_entry(self):
        """
        item cannot be too old, and cannot be too new
        """
        date_1 = DateUtils.get_datetime_now_utc() - timedelta(days=2)
        date_2 = DateUtils.get_datetime_now_utc() - timedelta(minutes=2)
        date_3 = DateUtils.get_datetime_now_utc() - timedelta(seconds=2)

        UserEntryVisits.objects.create(user="test_username", visits = 2, date_last_visit = date_1, entry_object = self.youtube_object)
        UserEntryVisits.objects.create(user="test_username", visits = 2, date_last_visit = date_2, entry_object = self.tiktok_object)
        UserEntryVisits.objects.create(user="test_username", visits = 2, date_last_visit = date_3, entry_object = self.odysee_object)

        # call tested function
        entry = UserEntryVisits.get_last_user_entry("test_username")

        self.assertTrue(entry)
        self.assertEqual(entry, self.tiktok_object)

    def test_entry_get_last_user_entry_not_found(self):
        UserEntryVisits.objects.create(user="test_username", visits = 2, date_last_visit = DateUtils.get_datetime_now_utc() - timedelta(hours=2), entry_object = self.youtube_object)

        # call tested function
        entry = UserEntryVisits.get_last_user_entry("test_username")

        self.assertFalse(entry)
