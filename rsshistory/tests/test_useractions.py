from datetime import timedelta
from django.test import TestCase

from ..controllers import LinkDataController, SourceDataController, DomainsController
from ..configuration import Configuration
from ..models import LinkTagsDataModel
from ..dateutils import DateUtils


class LinkTagsDataModelTest(TestCase):
    def setUp(self):
        c = Configuration.get_object()

        current_time = DateUtils.get_datetime_now_utc()
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

        self.entry = LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=bookmarked",
            title="The first link",
            source_obj=source_youtube,
            bookmarked=True,
            language="en",
            domain_obj=domain,
            date_published=current_time,
        )

    def test_set_tags(self):
        LinkTagsDataModel.objects.all().delete()

        data = {}
        data["author"] = "testuser"
        data["tag"] = "tag1, tag2"
        data["entry"] = self.entry

        # call tested function
        LinkTagsDataModel.set_tags(data)

        tags = LinkTagsDataModel.objects.all()

        self.assertEqual(tags.count(), 2)
        self.assertEqual(tags[0].tag, "tag1")
        self.assertEqual(tags[0].link_obj, self.entry)
        self.assertEqual(tags[1].tag, "tag2")
        self.assertEqual(tags[1].link_obj, self.entry)

    def test_set_tags_map(self):
        LinkTagsDataModel.objects.all().delete()

        data = {}
        data["author"] = "testuser"
        data["tags"] = ["tag1", "tag2"]
        data["entry"] = self.entry

        # call tested function
        LinkTagsDataModel.set_tags_map(data)

        tags = LinkTagsDataModel.objects.all()

        self.assertEqual(tags.count(), 2)
        self.assertEqual(tags[0].tag, "tag2")
        self.assertEqual(tags[0].link_obj, self.entry)
        self.assertEqual(tags[1].tag, "tag1")
        self.assertEqual(tags[1].link_obj, self.entry)

    def test_set_tag(self):
        LinkTagsDataModel.objects.all().delete()

        # call tested function
        LinkTagsDataModel.set_tag(self.entry, "tag3", "testuser2")
        LinkTagsDataModel.set_tag(self.entry, "tag4", "testuser2")

        tags = LinkTagsDataModel.objects.all()

        self.assertEqual(tags.count(), 2)
        self.assertEqual(tags[0].tag, "tag4")
        self.assertEqual(tags[0].link_obj, self.entry)
        self.assertEqual(tags[1].tag, "tag3")
        self.assertEqual(tags[1].link_obj, self.entry)
