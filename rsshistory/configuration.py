from datetime import datetime
from pathlib import Path
import logging

from django.contrib.auth.models import User

from utils.dateutils import DateUtils
from utils.logger import Logger

from .models import ConfigurationEntry, SystemOperation
from .apps import LinkDatabase

"""
version is split into three digits:
 - release
 - model version
 - patch

 if there is a small incremental change bump up the patch number
 if a change requires the model to be changed, then second digit is updated, patch is set to 0
 if something should be released to public, then release version changes
"""
__version__ = "0.82.0"


class Configuration(object):
    obj = {}

    def __init__(self, app_name=LinkDatabase.name):
        self.app_name = str(app_name)
        self.directory = Path(".")
        self.version = __version__

        self.enable_logging()

        self.context = {}
        self.config_entry = ConfigurationEntry.get()
        self.get_context()

        self.apply_webconfig()

    def get_context_minimal():
        config_entry = ConfigurationEntry.get()
        return {
            "page_title": "[{}]".format(LinkDatabase.name),
            "app_name": str(LinkDatabase.name),
            "app_title": config_entry.instance_title,
            "app_description": config_entry.instance_description,
            "admin_email": "renegat@renegat0x0.ddns.net",
            "admin_user": config_entry.admin_user,
            "app_version": __version__,
            "config": config_entry,
            "base_generic": str(Path(LinkDatabase.name) / "base_generic.html"),
        }

    def get_context(self):
        if len(self.context) == 0:
            config_entry = ConfigurationEntry.get()

            self.context = {
                "page_title": "[{}]".format(self.app_name),
                "app_name": str(self.app_name),
                "app_title": config_entry.instance_title,
                "app_description": config_entry.instance_description,
                "admin_email": "renegat@renegat0x0.ddns.net",
                "admin_user": self.config_entry.admin_user,
                "app_version": self.version,
                "config": self.config_entry,
                "base_generic": str(Path(self.app_name) / "base_generic.html"),
                "c": self,
            }
        else:
            return self.context

    def get_object(app_name=None):
        if app_name is None:
            from .apps import LinkDatabase

            app_name = LinkDatabase.name

        app_name = str(app_name)

        if app_name not in Configuration.obj:
            c = Configuration(app_name)
            Configuration.obj[app_name] = c

        return Configuration.obj[app_name]

    def get_workspaces(self):
        result = []
        items_in_dir = os.listdir(self.directory)
        for item in items_in_dir:
            full_path_item = item + "/apps.py"
            if os.path.isfile(full_path_item):
                if item != "private":
                    result.append(item)

        return result

    def enable_logging(self):
        from .models import AppLogging
        Logger.app_logger = AppLogging

    def apply_webconfig(self):
        self.apply_ssl_verification()
        self.apply_user_agent()
        self.apply_robots_txt()
        self.apply_web_logger()
        self.apply_crawling_scripts()

        from webtools import WebConfig
        c = self.config_entry
        WebConfig.selenium_driver_location = c.selenium_driver_path

    def apply_ssl_verification(self):
        from webtools import HttpPageHandler

        if not self.config_entry.ssl_verification:
            HttpPageHandler.disable_ssl_warnings()

    def apply_user_agent(self):
        from webtools import HttpPageHandler

        HttpPageHandler.user_agent = self.config_entry.user_agent

    def apply_crawling_scripts(self):
        from webtools import WebConfig

        c = self.config_entry

        WebConfig.crawling_full_script = c.crawling_full_script
        WebConfig.crawling_headless_script = c.crawling_headless_script
        WebConfig.crawling_server_port = c.crawling_server_port

    def apply_robots_txt(self):
        from webtools import DomainCache

        DomainCache.respect_robots_txt = self.config_entry.respect_robots_txt

    def apply_web_logger(self):
        from webtools import WebConfig
        from .models import AppLogging

        WebConfig.use_logger(AppLogging)

    def get_export_path(self, append=False):
        directory = Path(ConfigurationEntry.get().data_export_path)
        if append:
            return directory / self.app_name / append
        else:
            return directory / self.app_name

    def get_import_path(self, append=False):
        directory = Path(ConfigurationEntry.get().data_import_path)
        if append:
            return directory / self.app_name / append
        else:
            return directory / self.app_name

    def get_data_path(self):
        return self.directory / "data" / self.app_name

    def get_sources_file_name(self):
        return "sources.json"

    def get_domains_file_name(self):
        return "domains.json"

    def get_personal_domains_file_name(self):
        return "domains_personal.json"

    def get_keywords_file_name(self):
        return "keywords.json"

    def get_daily_data_day_path(self, day_iso=None):
        if day_iso == None:
            day_iso = DateUtils.get_date_today().isoformat()

        in_date = datetime.fromisoformat(day_iso)
        in_tuple = DateUtils.get_date_tuple(in_date)

        day_path = Path(in_tuple[0]) / in_tuple[1] / Path(day_iso)
        return day_path

    def get_url_clean_name(self, file_name):
        file_name = (
            file_name.replace(":", ".")
            .replace("/", ".")
            .replace("\\", ".")
            .replace("?", ".")
            .replace("=", ".")
        )

        return file_name

    def get_superuser(self):
        users = User.objects.filter(is_superuser=True)
        if users.count() > 0:
            return users[0]

    def get_local_time(self, utc_time):
        """
        We can configure system to display various time zones
        @return time string, in local time
        """
        config = self.config_entry
        time_zone = config.time_zone

        return DateUtils.get_local_time(utc_time, time_zone)

    def get_local_time_object(self, utc_time):
        """
        We can configure system to display various time zones
        @return time string, in local time
        """
        config = self.config_entry
        time_zone = config.time_zone

        return DateUtils.get_local_time_object(utc_time, time_zone)

    def get_blocked_keywords(self):
        result = []
        if self.config_entry.block_keywords:
            keywords = self.config_entry.block_keywords.split(",")
            for keyword in keywords:
                result.append(keyword.strip())
        return result

    def refresh(self, thread_id):
        if thread_id == 0:
            if self.is_it_time_to_ping:
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

    def is_it_time_to_ping(self):
        datetime = SystemOperation.get_last_internet_check()
        if not datetime:
            return True

        timedelta = DateUtils.get_datetime_now_utc() - datetime
        if (timedelta.seconds / 60) > 15:
            return True
        return False

    def ping_internet(self, thread_id):
        # TODO this should be done by Url. ping

        from webtools import HttpRequestBuilder

        test_page_url = self.config_entry.internet_test_page

        p = HttpRequestBuilder(url=test_page_url)
        return p.ping()

    def encrypt(self, message):
        from django.conf import settings
        from cryptography.fernet import Fernet

        key = settings.SECRET_KEY

        fernet = Fernet(key)
        return fernet.encrypt(message.encode())

    def decrypt(self, message):
        from cryptography.fernet import Fernet

        key = settings.SECRET_KEY

        fernet = Fernet(key)
        return fernet.decrypt(message).decode()

    def get_thread_info(self, display=True):
        """
        @display If true, then provide dates meant for display (local time)
        """
        result = []
        for thread in SystemOperation.get_thread_ids():
            date = SystemOperation.get_last_thread_signal(thread)
            if date:
                date = self.get_local_time(date)

            result.append([thread, date])

        return result
