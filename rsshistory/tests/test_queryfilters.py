
from pathlib import Path
import shutil
from datetime import datetime

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from ..controllers import SourceDataController, LinkDataController
from ..queryfilters import SourceFilter, EntryFilter


class FiltersTest(TestCase):
    def setUp(self):
        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )
        LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=persistent",
            title="The first link",
            source_obj=source_youtube,
            persistent=True,
            date_published=datetime.strptime("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=nonpersistent",
            title="The second link",
            source_obj=source_youtube,
            persistent=False,
            date_published=datetime.strptime("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        SourceDataController.objects.create(
            url="https://linkedin.com",
            title="LinkedIn",
            category="No",
            subcategory="No",
            export_to_cms=False,
        )

    def test_source_filters(self):
        args = {'title' : 'link', "category" : "none", "subcategory" : "none", "notsupported" : "none"}

        thefilter = SourceFilter(args)

        filter_args = thefilter.get_filter_args()

        self.assertTrue( "title" in filter_args)
        self.assertTrue( "category" in filter_args)
        self.assertTrue( "subcategory" in filter_args)

        self.assertTrue( "unsupported" not in filter_args)

    def test_source_filters_translate(self):
        args = {'title' : 'link', "category" : "none", "subcategory" : "none", "notsupported" : "none"}

        thefilter = SourceFilter(args)

        filter_args = thefilter.get_filter_args(True)

        self.assertTrue( "title" in filter_args)
        self.assertTrue( "category" in filter_args)
        self.assertTrue( "subcategory" in filter_args)

        self.assertTrue( "unsupported" not in filter_args)

    def test_entry_filters(self):

        args = {'title' : 'link',
                "language" : "none",
                "user" : "none",
                "tag" : "none",
                "vote" : "none",
                "source_title" : "none",
                "persistent" : "none",
                "category" : "none",
                "subcategory" : "none",
                "artist" : "none",
                "album" : "none",
                "date_from" : "none",
                "date_to" : "none",
                "archive" : "none",
                "unsupported" : "none",
                }

        thefilter = EntryFilter(args)

        filter_args = thefilter.get_entry_filter_args()

        self.assertTrue( "title" in filter_args)
        self.assertTrue( "language" in filter_args)
        self.assertTrue( "user" in filter_args)
        self.assertTrue( "tag" in filter_args)
        self.assertTrue( "vote" in filter_args)
        self.assertTrue( "source_title" in filter_args)
        self.assertTrue( "persistent" in filter_args)
        self.assertTrue( "category" in filter_args)
        self.assertTrue( "subcategory" in filter_args)
        self.assertTrue( "artist" in filter_args)
        self.assertTrue( "album" in filter_args)
        self.assertTrue( "date_from" in filter_args)
        self.assertTrue( "date_to" in filter_args)
        self.assertTrue( "archive" in filter_args)

        self.assertTrue( "unsupported" not in filter_args)

    def test_entry_filters_translate(self):

        args = {'title' : 'link',
                "language" : "none",
                "user" : "none",
                "tag" : "none",
                "vote" : "none",
                "category" : "none",
                "subcategory" : "none",
                "source_title" : "none",
                "persistent" : "none",
                "artist" : "none",
                "album" : "none",
                "date_from" : "none",
                "date_to" : "none",
                "archive" : "none",
                "unsupported" : "none",
                }

        thefilter = EntryFilter(args)

        filter_args = thefilter.get_entry_filter_args(True)

        self.assertTrue( "title__icontains" in filter_args)
        self.assertTrue( "language__icontains" in filter_args)
        self.assertTrue( "user__icontains" in filter_args)
        self.assertTrue( "tags__tag__icontains" in filter_args)
        self.assertTrue( "votes__vote__gt" in filter_args)
        self.assertTrue( "source_obj__title" in filter_args)
        self.assertTrue( "source_obj__category" in filter_args)
        self.assertTrue( "source_obj__subcategory" in filter_args)
        self.assertTrue( "persistent" in filter_args)
        self.assertTrue( "artist__icontains" in filter_args)
        self.assertTrue( "album__icontains" in filter_args)
        self.assertTrue( "date_published__range" in filter_args)

        # archive is a filter thing, should not be used in queries
        self.assertTrue( "archive" not in filter_args)

        self.assertTrue( "unsupported" not in filter_args)

    def test_entry_source_filters(self):
        args = {
                "category" : "none",
                "subcategory" : "none",
                "source_title" : "none",

                "unsupported" : "none",
                }

        thefilter = EntryFilter(args)

        filter_args = thefilter.get_source_filter_args()

        self.assertTrue( "category" in filter_args)
        self.assertTrue( "subcategory" in filter_args)
        self.assertTrue( "source_title" in filter_args)

        self.assertTrue( "unsupported" not in filter_args)

    def test_source_filter_limit(self):
        args = {'title' : 'link', "category" : "none", "subcategory" : "none", "notsupported" : "none", "page" : "1"}

        thefilter = SourceFilter(args)
        limit = thefilter.get_limit()

        self.assertEqual(limit[0], 0)
        self.assertEqual(limit[1], 100)

        args = {'title' : 'link', "category" : "none", "subcategory" : "none", "notsupported" : "none", "page" : "2"}

        thefilter = SourceFilter(args)
        limit = thefilter.get_limit()

        self.assertEqual(limit[0], 100)
        self.assertEqual(limit[1], 200)

    def test_entry_filter_limit(self):
        args = {'title' : 'link', "category" : "none", "subcategory" : "none", "notsupported" : "none", "page" : "1"}

        thefilter = EntryFilter(args)
        limit = thefilter.get_limit()

        self.assertEqual(limit[0], 0)
        self.assertEqual(limit[1], 100)

        args = {'title' : 'link', "category" : "none", "subcategory" : "none", "notsupported" : "none", "page" : "2"}

        thefilter = EntryFilter(args)
        limit = thefilter.get_limit()

        self.assertEqual(limit[0], 100)
        self.assertEqual(limit[1], 200)
