from datetime import timedelta
from django.contrib.auth.models import User

from utils.dateutils import DateUtils

from ..controllers import LinkDataController
from ..models import SocialData
from ..configuration import Configuration

from .fakeinternet import FakeInternetTestCase


class SocialDataTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()
        self.setup_configuration()

        self.user = User.objects.create_user(
            username="TestUser", password="testpassword", is_staff=True
        )

    def test_create(self):

        entry = LinkDataController.objects.create(
            source_url="https://notsupported.com",
            link="https://notsupported.com/watch?v=bookmarked",
            title="The first link",
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        data = {"followers_count" : None,
                "rating" : None,
                "stars" : None,
                "thumbs_down" : 457784,
                "thumbs_up": 15783577,
                "upvote_ratio": 0.9718136922145872,
                "upvote_view_ratio": 0.006968351041263936,
                "view_count": 2265037583,
                "entry" : entry}
        item = SocialData.objects.create(**data)

        self.assertEqual(SocialData.objects.all().count(), 1)

    def test_get__unsupported(self):

        entry = LinkDataController.objects.create(
            source_url="https://notsupported.com",
            link="https://notsupported.com/watch?v=bookmarked",
            title="The first link",
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        # call tested function
        social_data = SocialData.get(entry)

        self.assertFalse(social_data)

    def test_is_supported__github(self):
        entry = LinkDataController.objects.create(
            source_url="",
            link="https://github.com/rumca-js/Django-link-archive",
        )

        # call tested function
        status = SocialData.is_supported(entry)

        self.assertTrue(status)

    def test_is_supported__youtube(self):
        entry = LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com/watch?v=bookmarked",
            title="The first link",
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        # call tested function
        status = SocialData.is_supported(entry)

        self.assertTrue(status)

    def test_is_supported__reddit(self):
        entry = LinkDataController.objects.create(
            link="https://www.reddit.com/r/redditdev/comments/1hw8p3j/i_used_the_reddit_api_to_save_myself_time_with_my",
            title="The second link",
            bookmarked=False,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        # call tested function
        status = SocialData.is_supported(entry)

        self.assertTrue(status)

    def test_get__github(self):
        entry = LinkDataController.objects.create(
            source_url="",
            link="https://github.com/rumca-js/Django-link-archive",
        )

        # call tested function
        social_data = SocialData.get(entry)

        self.assertFalse(social_data)

    def test_get__youtube(self):
        entry = LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com/watch?v=bookmarked",
            title="The first link",
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        # call tested function
        social_data = SocialData.get(entry)

        self.assertFalse(social_data)

    def test_get__reddit(self):
        entry = LinkDataController.objects.create(
            link="https://www.reddit.com/r/redditdev/comments/1hw8p3j/i_used_the_reddit_api_to_save_myself_time_with_my",
            title="The second link",
            bookmarked=False,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        # call tested function
        social_data = SocialData.get(entry)

        self.assertFalse(social_data)

    def test_update__github(self):
        entry = LinkDataController.objects.create(
            source_url="",
            link="https://github.com/rumca-js/Django-link-archive",
        )

        # call tested function
        social_data = SocialData.update(entry)

        self.assertTrue(social_data)
        self.assertTrue(social_data.stars)

    def test_update__youtube(self):
        entry = LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com/watch?v=bookmarked",
            title="The first link",
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        social_data = SocialData.objects.create(view_count=1, entry=entry)

        # call tested function
        social_data = SocialData.update(entry)

        self.assertTrue(social_data)

    def test_cleanup(self):
        entry = LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com/watch?v=bookmarked",
            title="The first link",
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        # call tested function
        status = SocialData.cleanup()
        self.assertTrue(status)

    def test_truncate(self):
        entry = LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com/watch?v=bookmarked",
            title="The first link",
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        # call tested function
        status = SocialData.truncate()
        self.assertEqual(SocialData.objects.all().count(), 0)
