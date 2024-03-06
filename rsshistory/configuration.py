from datetime import datetime
from pathlib import Path
import logging

from .basictypes import *
from .models import ConfigurationEntry, UserConfig
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
__version__ = "0.49.0"


from pathlib import Path


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
        self.apply_ssl_verification()
        self.apply_user_agent()

    def get_context(self):
        if len(self.context) == 0:
            self.context = {
                "page_title": "[{}]".format(self.app_name),
                "app_name": str(self.app_name),
                "app_title": "Personal Link Database",
                "app_description": "Personal Link Database. May work as link aggregator, may link as YouTube subscription filter.",
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
        pass

    def apply_ssl_verification(self):
        from .webtools import BasePage

        if not self.config_entry.ssl_verification:
            BasePage.disable_ssl_warnings()

    def apply_user_agent(self):
        from .webtools import BasePage

        BasePage.user_agent = self.config_entry.user_agent

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
        from .dateutils import DateUtils

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
