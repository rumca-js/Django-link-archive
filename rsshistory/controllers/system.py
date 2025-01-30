from utils.dateutils import DateUtils

from ..models import (
    ConfigurationEntry,
    SystemOperation,
    AppLogging,
)


class SystemOperationController(object):

    def refresh(self, thread_id):
        if thread_id == "RefreshProcessor":
            if self.is_it_time_to_ping():
                if self.ping_internet(thread_id):
                    SystemOperation.add_by_thread(
                        thread_id, internet_status_checked=True, internet_status_ok=True
                    )
                else:
                    SystemOperation.add_by_thread(
                        thread_id,
                        internet_status_checked=True,
                        internet_status_ok=False,
                    )
        else:
            SystemOperation.add_by_thread(thread_id)

    def cleanup(cfg=None, thread_ids=None):
        if not thread_ids:
            return

        thread_ids = SystemOperationController.threads_to_threads(thread_ids)

        for thread_id in thread_ids:
            # leave one entry with time check
            all_entries = SystemOperation.objects.filter(
                thread_id=thread_id, is_internet_connection_checked=True
            )
            if all_entries.exists() and all_entries.count() > 1:
                entries = all_entries[1:]
                for entry in entries:
                    entry.delete()

            # leave one entry without time check
            all_entries = SystemOperation.objects.filter(
                thread_id=thread_id, is_internet_connection_checked=False
            )
            if all_entries.exists() and all_entries.count() > 1:
                entries = all_entries[1:]
                for entry in entries:
                    entry.delete()

    def is_it_time_to_ping(self):
        datetime = self.get_last_internet_check()
        if not datetime:
            return True

        timedelta = DateUtils.get_datetime_now_utc() - datetime
        if (timedelta.seconds / 60) > 15:
            return True
        return False

    def ping_internet(self, thread_id):
        # TODO this should be done by Url. ping

        config_entry = ConfigurationEntry.get()

        test_page_url = config_entry.internet_status_test_url

        from ..pluginurl import UrlHandlerEx

        if not UrlHandlerEx.ping(test_page_url):
            AppLogging.error("Cannot ping test page {}".format(test_page_url))
            return False
        return True

    def is_internet_ok(self):
        """
        TODO - we do not know when we started APP.
        """
        return self.ping_internet(2)

    def is_remote_server_down(self):
        config_entry = ConfigurationEntry.get()

        remote_server = config_entry.remote_webtools_server_location

        if not remote_server:
            return False

        from ..pluginurl import UrlHandlerEx

        if not UrlHandlerEx.ping(remote_server):
            AppLogging.error("Cannot ping remote server: {}".format(remote_server))
            return True

        return False

    def is_system_healthy(self, thread_ids):
        c = ConfigurationEntry.get()
        if c.enable_background_jobs:
            if not self.is_internet_ok():
                return False
            if not self.is_threading_ok(thread_ids):
                return False

    def is_threading_ok(self, thread_ids=None):
        hours_limit = 1800

        if thread_ids is None:
            return False

        thread_ids = SystemOperationController.threads_to_threads(thread_ids)

        for thread_id in thread_ids:
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

    def get_last_internet_check(self):
        entries = SystemOperation.objects.filter(is_internet_connection_checked=True)

        if entries.exists():
            return entries[0].date_created

    def get_last_internet_status(self):
        entries = SystemOperation.objects.filter(is_internet_connection_checked=True)

        if entries.exists():
            return entries[0].is_internet_connection_ok

    def get_thread_info(self, thread_ids=None):
        """
        @display If true, then provide dates meant for display (local time)
        """
        result = []

        thread_ids = SystemOperationController.threads_to_threads(thread_ids)

        for thread in thread_ids:
            date = self.get_last_thread_signal(thread)
            result.append([thread, date])

        return result

    def threads_to_threads(threads):
        thread_ids = []

        for thread in threads:
            thread_ids.append(thread[1].__name__)

        return thread_ids
