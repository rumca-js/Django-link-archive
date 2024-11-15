from utils.dateutils import DateUtils

from ..models import SystemOperation, ConfigurationEntry, AppLogging


class SystemOperationController(object):

    def is_system_healthy():
        from ..configuration import Configuration
        config = Configuration.get_object().config_entry
        if config.background_tasks:
            if not SystemOperationController.is_internet_ok():
                return False
            if not SystemOperationController.is_threading_ok():
                return False

    def is_threading_ok():
        hours_limit = 1800

        thread_ids = SystemOperationController.get_task_names()

        for thread_id in thread_ids:
            date = SystemOperationController.get_last_thread_signal(thread_id)
            if not date:
                return False

            delta = DateUtils.get_datetime_now_utc() - date

            if delta.total_seconds() > hours_limit:
                return False

        return True

    def is_internet_ok():
        statuses = SystemOperation.objects.filter(is_internet_connection_checked=True)
        if statuses.exists():
            status = statuses[0]

            delta = DateUtils.get_datetime_now_utc() - status.date_created

            hours_limit = 3600  # TODO hardcoded refresh task should be running more often than 1 hour?

            if delta.total_seconds() > hours_limit:
                status_is_valid = False
                return False

            return status.is_internet_connection_ok
        else:
            return True

    def get_last_thread_signal(thread_id):
        entries = SystemOperation.objects.filter(thread_id=thread_id)

        if entries.exists():
            return entries[0].date_created

    def get_last_internet_check():
        entries = SystemOperation.objects.filter(is_internet_connection_checked=True)

        if entries.exists():
            return entries[0].date_created

    def get_last_internet_status():
        entries = SystemOperation.objects.filter(is_internet_connection_checked=True)

        if entries.exists():
            return entries[0].is_internet_connection_ok

    def add_by_thread(
        thread_id, internet_status_checked=False, internet_status_ok=True
    ):
        # delete all entries without internet check
        all_entries = SystemOperation.objects.filter(
            thread_id=thread_id, is_internet_connection_checked=False
        )
        all_entries.delete()

        # leave one entry with time check
        all_entries = SystemOperation.objects.filter(
            thread_id=thread_id, is_internet_connection_checked=True
        )
        if all_entries.exists() and all_entries.count() > 1:
            entries = all_entries[1:]
            for entry in entries:
                entry.delete()

        SystemOperation.objects.create(
            thread_id=thread_id,
            is_internet_connection_checked=internet_status_checked,
            is_internet_connection_ok=internet_status_ok,
        )

    def get_task_names():
        try:
            from ..threadprocessors import get_task_names
            return get_task_names()
        except Exception as E:
            AppLogging.exc(E)

            return []

    def cleanup(cfg=None):
        thread_ids = SystemOperationController.get_task_names()
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

    def ping_internet(thread_id):
        # TODO this should be done by Url. ping
        from ..pluginurl import UrlHandler
        from ..configuration import Configuration

        config = Configuration.get_object().config_entry
        test_page_url = config.internet_test_page

        p = UrlHandler(url=test_page_url)
        # TODO fix this
        # return p.ping()
        return p.get_response().is_valid()

    def refresh(thread_id):
        if thread_id == "RefreshProcessor":
            if SystemOperationController.is_it_time_to_ping():
                if SystemOperationController.ping_internet(thread_id):
                    SystemOperationController.add_by_thread(
                        thread_id, internet_status_checked=True, internet_status_ok=True
                    )
                else:
                    SystemOperationController.add_by_thread(
                        thread_id,
                        internet_status_checked=True,
                        internet_status_ok=False,
                    )
        else:
            SystemOperationController.add_by_thread(thread_id)

    def is_it_time_to_ping():
        datetime = SystemOperationController.get_last_internet_check()
        if not datetime:
            return True

        timedelta = DateUtils.get_datetime_now_utc() - datetime
        if (timedelta.seconds / 60) > 15:
            return True
        return False

    def get_thread_info(display=True):
        """
        @display If true, then provide dates meant for display (local time)
        """
        result = []
        for thread in SystemOperationController.get_task_names():
            date = SystemOperationController.get_last_thread_signal(thread)
            result.append([thread, date])

        return result
