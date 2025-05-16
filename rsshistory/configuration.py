from datetime import datetime, timedelta
from pathlib import Path
import psutil
import os

from django.contrib.auth.models import User
from django.conf import settings

from utils.dateutils import DateUtils
from utils.logger import set_logger

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
__version__ = "2.11.3"


class Configuration(object):
    obj = {}

    def __init__(self, app_name=LinkDatabase.name):
        self.app_name = str(app_name)

        file_path = os.path.realpath(__file__)
        full_path = Path(file_path)
        self.directory = str(full_path.parents[1])

        self.version = __version__

        self.enable_logging()

        self.context = {}
        self.config_entry = ConfigurationEntry.get()
        self.get_context()
        self.nlps = {}

        self.apply_webconfig()

    def get_context_minimal():
        config_entry = ConfigurationEntry.get()
        return {
            "page_title": "[{}]".format(LinkDatabase.name),
            "app_name": str(LinkDatabase.name),
            "app_title": config_entry.instance_title,
            "app_description": config_entry.instance_description,
            "app_favicon": config_entry.favicon_internet_url,
            "admin_email": "renegat@renegat0x0.ddns.net",
            "admin_user": config_entry.admin_user,
            "app_version": __version__,
            "base_generic": str(Path(LinkDatabase.name) / "base_generic.html"),
        }

    def get_memory_usage(self):
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()

        # in bytes
        # print("RSS (Resident Set Size):", mem_info.rss)  # Actual physical memory used
        # print("VMS (Virtual Memory Size):", mem_info.vms)  # Total virtual memory used
        # print(f"Memory used (RSS): {mem_info.rss / (1024 * 1024):.2f} MB")

        return mem_info

    def is_memory_limit_reached(self):
        memory = self.get_memory_usage()

        resident = memory.rss / (1024 * 1024)
        virtual = memory.vms / (1024 * 1024)

        memory_threshold = self.config_entry.thread_memory_threshold

        if resident > memory_threshold or virtual > memory_threshold:
            return True
        return False

    def get_context(self):
        if len(self.context) == 0:
            self.context = Configuration.get_context_minimal()
            self.context["c"] = self
        else:
            return self.context

    def get_nlp(self, language):
        """
        nlp takes an awful lot of time to load
        https://stackoverflow.com/questions/43554124/is-possible-to-keep-spacy-in-memory-to-reduce-the-load-time
        """
        from .models import AppLogging

        try:
            if not language or language == "":
                return

            if language in self.nlps:
                return self.nlps[language]

            import spacy

            if language.find("en") >= 0:
                load_text = "en_core_web_sm"
            elif language.find("pl") >= 0:
                load_text = "pl_core_news_sm"
            else:
                return

            nlp = spacy.load(load_text)
            if nlp:
                self.nlps[language] = nlp
                return nlp

        except Exception as E:
            AppLogging.exc(E)
            return

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
        from .models import AppLoggingController

        set_logger(LinkDatabase.name, AppLoggingController())

    def apply_webconfig(self):
        from .models import Browser
        from .webtools import WebConfig

        self.apply_ssl_verification()
        self.apply_user_agent()
        self.apply_robots_txt()
        self.apply_web_logger()

        if Browser.objects.all().count() == 0:
            Browser.read_browser_setup()

    def apply_ssl_verification(self):
        from .webtools import WebConfig

        if not self.config_entry.ssl_verification:
            WebConfig.disable_ssl_warnings()

    def apply_user_agent(self):
        from .webtools import HttpPageHandler

        HttpPageHandler.user_agent = self.config_entry.user_agent

    def apply_robots_txt(self):
        from .webtools import DomainCache

        DomainCache.respect_robots_txt = self.config_entry.respect_robots_txt

    def apply_web_logger(self):
        from .webtools import WebConfig
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

    def get_settings(self, db_switch="default"):
        result = {}

        result["DATABASES"] = settings.DATABASES[db_switch]

        result["DEBUG"] = settings.DEBUG
        result["ALLOWED_HOSTS"] = settings.ALLOWED_HOSTS

        if hasattr(settings, "CELERY_BROKER_URL"):
            result["CELERY_BROKER_URL"] = settings.CELERY_BROKER_URL

        if hasattr(settings, "STATIC_URL"):
            result["STATIC_URL"] = settings.STATIC_URL

        if hasattr(settings, "TIME_ZONE"):
            result["TIME_ZONE"] = settings.TIME_ZONE

        if hasattr(settings, "USE_TZ"):
            result["USE_TZ"] = settings.USE_TZ

        if hasattr(settings, "USE_I18N"):
            result["USE_I18N"] = settings.USE_I18N

        if hasattr(settings, "LANGUAGE_CODE"):
            result["LANGUAGE_CODE"] = settings.LANGUAGE_CODE

        if hasattr(settings, "CELERY_RESULT_BACKEND"):
            result["CELERY_RESULT_BACKEND"] = settings.CELERY_RESULT_BACKEND

        if hasattr(settings, "CACHES"):
            result["CACHES"] = settings.CACHES

        return result

    def get_db_data(self, db_switch="default"):
        """
        result["USER"],
        result["DB"],
        """
        return settings.DATABASES[db_switch]

    def get_entry_remove_date(self):
        conf = self.config_entry

        if not conf.days_to_remove_links:
            return

        day_to_remove = DateUtils.get_datetime_now_utc() - timedelta(
            days=conf.days_to_remove_links
        )

        return day_to_remove

    def get_entry_move_to_archive_date(self):
        conf = self.config_entry

        if not conf.days_to_move_to_archive:
            return

        day_to_move = DateUtils.get_datetime_now_utc() - timedelta(
            days=conf.days_to_move_to_archive
        )

        return day_to_move
