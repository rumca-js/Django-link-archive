from datetime import datetime, timedelta
from datetime import date

from django.contrib.auth.models import User

from ..models import UserConfig
from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class UserTagsTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_get_age(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
            is_staff=True,
        )

        uc = UserConfig.objects.create(user=self.user)

        current_date = datetime.now().date()
        date_20_years_ago = current_date - timedelta(days=365 * 21)

        uc.birth_date = date_20_years_ago
        uc.save()

        # user is 20 years old
        # call tested function
        self.assertEqual(uc.get_age(), 20)

    def test_get_or_create(self):
        self.user = User.objects.create_user(
            username="testuser2",
            password="testpassword2",
            is_staff=True,
        )

        uc = UserConfig.get_or_create(self.user)
        self.assertTrue(uc)
