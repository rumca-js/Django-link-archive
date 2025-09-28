from django.urls import reverse
from django.contrib.auth.models import User

from utils.dateutils import DateUtils

from ..apps import LinkDatabase
from ..controllers import (
    SourceDataController,
    LinkDataController,
    DomainsController,
    BackgroundJobController,
)
from ..models import (
    KeyWords,
    DataExport,
    SourceCategories,
    SourceSubCategories,
    SourceOperationalData,
    Browser,
)

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class SocialDataViewsTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.user.is_staff = True
        self.user.save()

        # c = Configuration.get_object()
        # c.config_entry.logging_level = AppLogging.DEBUG
        # c.config_entry.save()

    def test_edit_form(self):
        SourceDataController.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        entry = LinkDataController.objects.create(
            link="https://linkedin.com",
            title="The first link",
            description="the first link description",
            source=None,
            bookmarked=False,
            permanent=False,
            date_published=DateUtils.get_datetime_now_utc(),
            language="en",
        )

        url = reverse("{}:social-data-edit".format(LinkDatabase.name), args=[entry.id])

        # call user action
        response = self.client.get(url)

        # print(response.text.decode('utf-8'))

        self.assertEqual(response.status_code, 200)
