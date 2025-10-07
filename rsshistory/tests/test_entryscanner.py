from datetime import timedelta
from django.contrib.auth.models import User

from utils.dateutils import DateUtils

from ..controllers import (
    EntryPageCrawler,
    SourceDataController,
    DomainsController,
    LinkDataController,
    ArchiveLinkDataController,
    BackgroundJobController,
)
from ..configuration import Configuration

from .fakeinternet import FakeInternetTestCase, DjangoRequestObject


class EntryPageCrawlerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()
        self.setup_configuration()

        c = Configuration.get_object()
        c.config_entry.track_user_actions = True
        c.config_entry.track_user_searches = True
        c.config_entry.track_user_navigation = True
        c.config_entry.save()

        self.source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            export_to_cms=True,
        )

        self.user_staff = User.objects.create_user(
            username="TestUser", password="testpassword", is_staff=True
        )
        self.user_not_staff = User.objects.create_user(
            username="TestUserNot", password="testpassword", is_staff=False
        )

    def clear(self):
        SourceDataController.objects.all().delete()
        LinkDataController.objects.all().delete()
        ArchiveLinkDataController.objects.all().delete()

    def create_entries(self, date_link_publish, date_to_remove):
        domain = DomainsController.objects.create(
            domain="https://youtube.com",
        )

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            export_to_cms=True,
            remove_after_days=1,
        )

        ob = LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=bookmarked",
            title="The first link",
            source=source_youtube,
            bookmarked=True,
            language="en",
            domain=domain,
            date_published=date_link_publish,
        )

        ob = LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=nonbookmarked",
            title="The second link",
            source=source_youtube,
            bookmarked=False,
            language="en",
            domain=domain,
            date_published=date_link_publish,
        )

        ob = LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=permanent",
            title="The first link",
            source=source_youtube,
            permanent=True,
            language="en",
            domain=domain,
            date_published=date_link_publish,
        )

        ob = ArchiveLinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=nonbookmarked2",
            title="The second link",
            source=source_youtube,
            bookmarked=False,
            language="en",
            domain=domain,
            date_published=date_to_remove,
        )

    def test_run__nodata(self):
        link_name = "https://youtube.com/v=12345"

        b = EntryPageCrawler(url=link_name)
        b.run()

        self.assertEqual(BackgroundJobController.objects.all().count(), 0)

    def test_run__nodata(self):
        link_name = "https://www.geekwire.com/feed"

        b = EntryPageCrawler(url=link_name)
        b.run()

        self.assertEqual(BackgroundJobController.objects.all().count(), 0)
