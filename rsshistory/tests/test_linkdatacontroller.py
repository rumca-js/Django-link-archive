from pathlib import Path
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from ..models import ConfigurationEntry, ArchiveLinkDataModel
from ..controllers import SourceDataController, LinkDataController
from ..configuration import Configuration
from ..dateutils import DateUtils
from .utilities import WebPageDisabled


class DataWriterTest(WebPageDisabled, TestCase):
    def setUp(self):
        self.disable_web_pages()

    def clear(self):
        SourceDataController.objects.all().delete()
        LinkDataController.objects.all().delete()
        ArchiveLinkDataModel.objects.all().delete()

    def create_entries(self, days_before):

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
            remove_after_days = 1,
        )
        LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=bookmarked",
            title="The first link",
            source_obj=source_youtube,
            bookmarked=True,
            date_published=days_before,
            language="en",
        )
        LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=nonbookmarked",
            title="The second link",
            source_obj=source_youtube,
            bookmarked=False,
            date_published=days_before,
            language="en",
        )
        LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=permanent",
            title="The first link",
            source_obj=source_youtube,
            permanent=True,
            date_published=days_before,
            language="en",
        )

    def test_move_old_links_to_archive(self):
        conf = Configuration.get_object().config_entry

        current_time = DateUtils.get_datetime_now_utc()
        days_before = current_time - timedelta(days = conf.days_to_move_to_archive + 1)

        self.clear()
        self.create_entries(days_before)

        LinkDataController.move_old_links_to_archive()

        bookmarked = LinkDataController.objects.filter(link = "https://youtube.com?v=bookmarked")
        self.assertEqual(bookmarked.count(), 1)
        permanent = LinkDataController.objects.filter(link = "https://youtube.com?v=permanent")
        self.assertEqual(permanent.count(), 1)
        nonbookmarked = LinkDataController.objects.filter(link = "https://youtube.com?v=nonbookmarked")
        self.assertEqual(nonbookmarked.count(), 0)

        self.assertEqual(ArchiveLinkDataModel.objects.all().count(), 1)

    def test_clear_old_entries(self):
        conf = Configuration.get_object().config_entry

        current_time = DateUtils.get_datetime_now_utc()
        days_before = current_time - timedelta(days = conf.days_to_remove_links + 1)

        self.clear()
        self.create_entries(days_before)

        LinkDataController.clear_old_entries()

        bookmarked = LinkDataController.objects.filter(link = "https://youtube.com?v=bookmarked")
        self.assertEqual(bookmarked.count(), 1)
        permanent = LinkDataController.objects.filter(link = "https://youtube.com?v=permanent")
        self.assertEqual(permanent.count(), 1)
        nonbookmarked = LinkDataController.objects.filter(link = "https://youtube.com?v=nonbookmarked")
        self.assertEqual(nonbookmarked.count(), 0)

        self.assertEqual(ArchiveLinkDataModel.objects.all().count(), 0)
