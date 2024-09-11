from datetime import timedelta
from django.contrib.auth.models import User

from utils.dateutils import DateUtils

from ..controllers import SourceDataController, LinkDataController
from ..models import ReadMarkers
from ..configuration import Configuration

from .fakeinternet import FakeInternetTestCase


class ReadMarkersTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()
        self.setup_configuration()

        self.user = User.objects.create_user(
            username="TestUser", password="testpassword", is_staff=True
        )

    def test_set__general_marker(self):
        ReadMarkers.objects.all().delete()

        # call tested function
        ReadMarkers.set(self.user)

        self.assertEqual(ReadMarkers.objects.all().count(), 1)

    def test_set__source_marker(self):
        ReadMarkers.objects.all().delete()

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )

        # call tested function
        ReadMarkers.set(self.user, source_youtube)

        self.assertEqual(ReadMarkers.objects.all().count(), 1)
