from django.contrib.auth.models import User
from datetime import timedelta
from django.test import TestCase

from ..controllers import LinkDataController, SourceDataController, DomainsController
from ..configuration import Configuration
from ..models import UserTags
from ..dateutils import DateUtils


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

        self.user = User.objects.create_user(
            username="test_username", password="testpassword"
        )

    def test_set_tags(self):
        UserTags.objects.all().delete()

        data = {}
        data["user"] = self.user
        data["tag"] = "tag1, tag2"
        data["entry"] = self.entry

        # call tested function
        UserTags.set_tags(data)

        tags = UserTags.objects.all()

        tag_names = [tag.tag for tag in tags]

        self.assertEqual(tags.count(), 2)
        self.assertTrue("tag1" in tag_names)
        self.assertTrue("tag2" in tag_names)
        self.assertEqual(tags[0].entry_object, self.entry)
        self.assertEqual(tags[1].entry_object, self.entry)

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
        self.assertEqual(tags[0].tag, "tag2")
        self.assertEqual(tags[0].entry_object, self.entry)
        self.assertEqual(tags[1].tag, "tag1")
        self.assertEqual(tags[1].entry_object, self.entry)

    def test_set_tag(self):
        UserTags.objects.all().delete()

        user = self.user

        # call tested function
        UserTags.set_tag(self.entry, "tag3", user)
        # call tested function
        UserTags.set_tag(self.entry, "tag4", user)

        tags = UserTags.objects.all()

        self.assertEqual(tags.count(), 2)
        self.assertEqual(tags[0].tag, "tag4")
        self.assertEqual(tags[0].entry_object, self.entry)
        self.assertEqual(tags[1].tag, "tag3")
        self.assertEqual(tags[1].entry_object, self.entry)
