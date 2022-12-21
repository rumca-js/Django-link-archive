import datetime
from datetime import date, timedelta
from pytz import timezone


class DateUtils(object):

    def __init__(self):
        pass

    def get_iso_today():
        return date.today().isoformat()

    def get_date_yesterday():
       current_date = date.today()
       prev_day = current_date - timedelta(days = 1) 

       return prev_day

    def get_date_today():
       return date.today()

    def get_date_tommorow():
       current_date = date.today()
       next_day = current_date + timedelta(days = 1)

       return next_day

    def get_datetime_now_utc():
        return datetime.datetime.now(timezone('UTC'))

    def get_datetime_file_name():
        return datetime.datetime.today().strftime('%Y-%m-%d_%H-%M-%S')

    def get_date_file_name():
        return DateUtils.format_date(datetime.datetime.today())

    def get_dir4date(date):
        return date.strftime('%Y-%m-%d')

    def get_iso_datetime(timestamp):
       from dateutil import parser
       date = parser.parse(timestamp)
       date = date.isoformat()
       return date

    def get_datetime_year(datetime):
        return datetime.strftime('%Y')

    def get_datetime_month(datetime):
        return datetime.strftime('%m')

    def get_range4day(date_iso):
       from datetime import date, timedelta
       current_date = date.fromisoformat(date_iso)
       next_day = current_date + timedelta(days = 1)

       return (current_date, next_day)

    def get_range_today():
       from datetime import date, timedelta

       current_date = date.today()
       return DateUtils.get_range4day(current_date.isoformat() )

    def is_month_changed():
        yesterday = DateUtils.get_date_yesterday()
        today = DateUtils.get_date_today()

        y_m = DateUtils.get_datetime_month(yesterday)
        t_m = DateUtils.get_datetime_month(today)

        if y_m != t_m:
            return True

        return False
