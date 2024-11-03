import json
from pathlib import Path
from django.contrib.auth.models import User

from utils.dateutils import DateUtils
from utils.services import ReadingList

from ..serializers import JsonImporter, MapImporter
from ..controllers import (
    LinkDataController,
    EntryDataBuilder,
    SourceDataBuilder,
    SourceDataController,
    SourceDataController,
    UserCommentsController,
    EntryWrapper,
)
from ..models import (
    UserVotes,
    UserTags,
)
from ..configuration import Configuration

from .fakeinternet import FakeInternetTestCase


entry_contents = """
[{"age": null, "album": null, "artist": null, "bookmarked": true, "comments": [], "date_published": "2024-06-19T22:43:38.594154+00:00", "description": "Description", "id": 153720, "language": "", "link": "https://linkedin.com", "manual_status_code": 0, "page_rating": 0, "page_rating_contents": 0, "page_rating_visits": 0, "page_rating_votes": 10, "permanent": true, "source_url": "", "status_code": 0, "tags": ["test1", "test2"], "thumbnail": null, "title": "Page Title", "vote": 0}]
"""


def import_from_data(user, contents, import_settings=None):
    data = json.loads(contents)

    entry_builder = EntryDataBuilder()
    source_builder = SourceDataBuilder()

    importer = MapImporter(
        user=user,
        entry_builder=entry_builder,
        source_builder=source_builder,
        import_settings=import_settings,
    )
    importer.import_from_data(data)


class JsonImporterTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="test_username", password="testpassword"
        )

    def test_import_from_data__entries(self):
        LinkDataController.objects.all().delete()
        UserVotes.objects.all().delete()
        UserTags.objects.all().delete()

        import_settings = {"import_entries" : True}

        # call tested functionality
        p = import_from_data(self.user, entry_contents, import_settings)

        links = LinkDataController.objects.all()

        self.assertEqual(len(links), 1)

        link = links[0]
        self.assertEqual(link.link, "https://linkedin.com")
        self.assertEqual(link.bookmarked, True)
        self.assertEqual(link.permanent, True)

        self.assertEqual(UserVotes.objects.all().count(), 0)
        self.assertEqual(UserTags.objects.all().count(), 0)

    def test_import_from_data__all(self):
        LinkDataController.objects.all().delete()
        UserVotes.objects.all().delete()
        UserTags.objects.all().delete()

        # by default import all
        import_settings = None

        # call tested functionality
        p = import_from_data(self.user, entry_contents, import_settings)

        links = LinkDataController.objects.all()

        self.assertEqual(len(links), 1)

        link = links[0]
        self.assertEqual(link.link, "https://linkedin.com")
        self.assertEqual(link.bookmarked, True)
        self.assertEqual(link.permanent, True)

        self.assertEqual(UserVotes.objects.all().count(), 1)
        self.assertEqual(UserTags.objects.all().count(), 2)
