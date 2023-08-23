from pathlib import Path
import shutil
from datetime import datetime, timedelta

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from ..dateutils import DateUtils


class DateUtilsTest(TestCase):
    def test_get_day_diff(self):
        input_time = DateUtils.get_datetime_now_utc() - timedelta(days=17)
        days = DateUtils.get_day_diff(input_time)

        self.assertTrue(days == 17)

        input_time = DateUtils.get_datetime_now_utc() - timedelta(days=19)
        days = DateUtils.get_day_diff(input_time)

        self.assertTrue(days == 19)
