from datetime import datetime
from utils.dateutils import DateUtils

from ..models import (
    SystemOperation,
    AppLogging,
    BackgroundJob,
    BackgroundJobHistory,
)
from ..configuration import Configuration
from .backgroundjob import BackgroundJobController


class SystemOperationController(object):

    def refresh(self, thread_id):
        # any thread can ping, check

        if self.is_it_time_to_ping():
            self.check_internet(thread_id)
            self.check_crawling_sever(thread_id)
        else:
            SystemOperation.add_by_thread(thread_id)

    def check_internet(self, thread_id):
        if self.ping_internet():
            SystemOperation.add_by_thread(
                thread_id, check_type=SystemOperation.CHECK_TYPE_INTERNET, status=True
            )
        else:
            SystemOperation.add_by_thread(
                thread_id,
                check_type=SystemOperation.CHECK_TYPE_INTERNET,
                status=False,
            )

    def check_crawling_sever(self, thread_id):
        """
        We do not want to use crawling server to check crawling server status
        """
        import requests

        config_entry = Configuration.get_object().config_entry

        remote_server = config_entry.remote_webtools_server_location

        if not remote_server:
            return False


        try:
            with requests.get(remote_server) as response:
                if response and response.status_code != 200:
                    SystemOperation.add_by_thread(
                        thread_id,
                        check_type=SystemOperation.CHECK_TYPE_CRAWLING_SERVER,
                        status=False,
                    )
                else:
                    SystemOperation.add_by_thread(
                        thread_id,
                        check_type=SystemOperation.CHECK_TYPE_CRAWLING_SERVER,
                        status=True,
                    )
        except Exception as E:
            AppLogging.exc(E)

    def cleanup(cfg=None, thread_ids=None):
        if thread_ids:
            # delete any obsolte
            current_thread_ids = SystemOperationController.get_threads()

            diff_elements = set(current_thread_ids) - set(thread_ids)
            for diff in diff_elements:
                rows = SystemOperation.objects.filter(thread_id=diff)
                rows.delete()
            return

        thread_ids = SystemOperationController.get_threads()

        check_types = SystemOperation.objects.values_list(
            "check_type", flat=True
        ).distinct()

        for thread_id in thread_ids:
            for check_type in check_types:
                # leave one entry
                all_entries = SystemOperation.objects.filter(
                    thread_id=thread_id, check_type=check_type
                )
                if all_entries.exists() and all_entries.count() > 1:
                    entries = all_entries[1:]
                    for entry in entries:
                        entry.delete()

    def is_it_time_to_ping(self):
        datetime = self.last_operation_status_date()
        if not datetime:
            return True

        timedelta = DateUtils.get_datetime_now_utc() - datetime
        if timedelta.seconds > 60:
            return True
        return False

    def ping_internet(self):
        # TODO this should be done by Url. ping

        config_entry = Configuration.get_object().config_entry

        test_page_url = config_entry.internet_status_test_url
        if test_page_url == "" or not test_page_url:
            return True

        from ..pluginurl import UrlHandlerEx

        if not UrlHandlerEx.ping(test_page_url):
            AppLogging.error("Cannot ping test page {}".format(test_page_url))
            return False
        return True

    def is_internet_ok(self):
        """
        TODO - we do not know when we started APP.
        """
        return self.last_operation_status()

    def is_remote_server_down(self):
        return not self.last_operation_status(
            check_type=SystemOperation.CHECK_TYPE_CRAWLING_SERVER
        )

    def is_system_healthy(self):
        config_entry = Configuration.get_object().config_entry

        if config_entry.enable_background_jobs:
            if not self.is_internet_ok():
                return False
            if not self.is_threading_ok():
                return False

    def is_threading_ok(self):
        hours_limit = 1800

        threads = SystemOperationController.get_threads()

        for thread_id in threads:
            if not self.is_thread_ok(thread_id):
                return False

        return True

    def is_thread_ok(self, thread_id):
        hours_limit = 1800

        date = self.get_last_thread_signal(thread_id)
        if not date:
            return False

        delta = DateUtils.get_datetime_now_utc() - date

        if delta.total_seconds() > hours_limit:
            return False

        return True

    def get_last_thread_signal(self, thread_id):
        entries = SystemOperation.objects.filter(thread_id=thread_id)

        if entries.exists():
            return entries[0].date_created

    def last_operation_status_date(
        self, check_type=SystemOperation.CHECK_TYPE_INTERNET
    ):
        entries = SystemOperation.objects.filter(check_type=check_type)

        if entries.exists():
            return entries[0].date_created

    def last_operation_status(self, check_type=SystemOperation.CHECK_TYPE_INTERNET):
        entries = SystemOperation.objects.filter(check_type=check_type)

        if entries.exists():
            return entries[0].status
        return True

    def get_thread_info(self, thread_id):
        """
        @display If true, then provide dates meant for display (local time)
        """
        date = self.get_last_thread_signal(thread_id)
        status = self.is_thread_ok(thread_id)
        return [thread_id, date, status]

    def get_threads():
        result = set()

        rows = SystemOperation.objects.all()
        for row in rows:
            result.add(row.thread_id)

        return sorted(result)

    def is_time_to_cleanup(self):
        today = datetime.today().date()

        config_entry = Configuration.get_object().config_entry
        cleanup_time = config_entry.cleanup_time

        new_cleanup_date = datetime.combine(today, cleanup_time)
        new_cleanup_date = DateUtils.to_utc_date(new_cleanup_date)

        # job without subject is main job

        jobs = BackgroundJobController.objects.filter(
            job=BackgroundJob.JOB_CLEANUP, subject="",
        )
        if jobs.exists():
            return False

        jobs = BackgroundJobHistory.objects.filter(
            job=BackgroundJob.JOB_CLEANUP, subject="", date_created__gt=new_cleanup_date
        )
        if jobs.exists():
            return False

        return True
