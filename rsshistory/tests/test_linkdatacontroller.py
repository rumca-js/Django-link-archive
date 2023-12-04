from pathlib import Path
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from ..models import ConfigurationEntry, ArchiveLinkDataModel
from ..controllers import SourceDataController, LinkDataController, DomainsController
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
        domain = DomainsController.objects.create(
                domain ="https://youtube.com",
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
            domain_obj = domain,
        )
        # TODO - check why that does not work out of the box!!!
        ob.date_published=days_before
        ob.save()

        ob = LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=nonbookmarked",
            title="The second link",
            source_obj=source_youtube,
            bookmarked=False,
            language="en",
            domain_obj = domain,
        )
        ob.date_published=days_before
        ob.save()

        ob = LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=permanent",
            title="The first link",
            source_obj=source_youtube,
            permanent=True,
            language="en",
            domain_obj = domain,
        )
        ob.date_published=days_before
        ob.save()

    def test_move_old_links_to_archive(self):
        conf = Configuration.get_object().config_entry

        current_time = DateUtils.get_datetime_now_utc()
        days_before = current_time - timedelta(days=conf.days_to_move_to_archive + 1)

        self.clear()
        self.create_entries(days_before)

        original_date_published = LinkDataController.objects.filter(
            link="https://youtube.com?v=nonbookmarked"
        )[0].date_published

        # call tested function
        LinkDataController.move_old_links_to_archive()

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

        archived = ArchiveLinkDataModel.objects.all()
        domains = DomainsController.objects.all()

        self.assertEqual(archived.count(), 1)
        self.assertEqual(domains.count(), 1)
        self.assertEqual(archived[0].domain_obj, domains[0])
        self.assertEqual(archived[0].date_published, original_date_published)

    def test_clear_old_entries(self):
        conf = Configuration.get_object().config_entry

        current_time = DateUtils.get_datetime_now_utc()
        days_before = current_time - timedelta(days=conf.days_to_remove_links + 2)

        self.clear()
        self.create_entries(days_before)

        # call tested function
        LinkDataController.clear_old_entries()

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
        self.assertEqual(ArchiveLinkDataModel.objects.all().count(), 0)
