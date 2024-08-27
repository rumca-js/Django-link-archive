from datetime import timedelta

from utils.dateutils import DateUtils

from .fakeinternet import FakeInternetTestCase


class DateUtilsTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_get_day_diff(self):
        input_time = DateUtils.get_datetime_now_utc() - timedelta(days=17)
        days = DateUtils.get_day_diff(input_time)

        self.assertTrue(days == 17)

        input_time = DateUtils.get_datetime_now_utc() - timedelta(days=19)
        days = DateUtils.get_day_diff(input_time)

        self.assertTrue(days == 19)
