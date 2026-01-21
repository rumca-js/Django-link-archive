from datetime import datetime, date, timedelta
import os
import traceback

from django.db import models
from django.urls import reverse
from django.db.models import Q

from webtoolkit import UrlLocation
from utils.dateutils import DateUtils

from ..models import (
    LinkDataModel,
    AppLogging,
    SourceDataModel,
    SourceOperationalData,
    SourceCategories,
    SourceSubCategories,
)
from .backgroundjob import (
    BackgroundJobController,
)

from ..configuration import Configuration
from ..apps import LinkDatabase


class SourceDataController(SourceDataModel):
    class Meta:
        proxy = True

    def cleanup(cfg=None):
        SourceDataModel.reset_categories()

        sources = SourceDataModel.objects.filter(enabled=True)

        for source in sources:
            entries = LinkDataModel.objects.filter(link=source.url)
            if not entries.exists():
                BackgroundJobController.source_link_add(source)
            else:
                entry = entries[0]
                entry.permanent = True
                entry.save()

    def truncate(cfg=None):
        sources = Q()
        if cfg:
            if "enabled" in cfg:
                if cfg["enabled"] == True:
                    sources = SourceDataController.objects.filter(enabled=True)
                else:
                    sources = SourceDataController.objects.filter(enabled=False)
            else:
                sources = SourceDataController.objects.all()

        if sources.exists():
            for source in sources:
                source.custom_remove()

        return True

    def get_days_to_remove(self):
        days = self.remove_after_days
        return days

    def get_long_description(self):
        return "Category:{} Subcategory:{} Export:{} Enabled:{} Type:{}".format(
            self.category_name,
            self.subcategory_name,
            self.export_to_cms,
            self.enabled,
            self.source_type,
        )

    def get_full_description(self):
        return "{} Export:{} Fetched:{} Number of entries:{} Import seconds:{}".format(
            self.get_long_description(),
            self.export_to_cms,
            self.get_date_fetched(),
            self.get_number_of_entries(),
            self.get_import_seconds(),
        )

    def is_fetch_possible(self):
        if not self.enabled:
            return False

        now = DateUtils.get_datetime_now_utc()
        date_fetched = self.get_date_fetched()

        if date_fetched:
            time_since_update = now - date_fetched
            # mins = time_since_update / timedelta(minutes=1)
            secs = time_since_update / timedelta(seconds=1)

            if secs >= self.fetch_period:
                return True
            return False

        return True

    def is_removable(self):
        """
        TODO rename this function
        """
        days = self.get_days_to_remove()

        if days > 0:
            return True
        else:
            return False

    def get_dynamic_data(self):
        if hasattr(self, "dynamic_data"):
            return self.dynamic_data

    def get_date_fetched(self):
        obj = self.get_dynamic_data()
        if obj:
            return obj.date_fetched

    def get_page_hash(self):
        obj = self.get_dynamic_data()
        if obj:
            return obj.page_hash

    def get_body_hash(self):
        obj = self.get_dynamic_data()
        if obj:
            return obj.body_hash

    def get_import_seconds(self):
        obj = self.get_dynamic_data()
        if obj:
            return obj.import_seconds

    def get_number_of_entries(self):
        obj = self.get_dynamic_data()
        if obj:
            return obj.number_of_entries

    def set_operational_info(
        self,
        date_fetched,
        number_of_entries,
        import_seconds,
        hash_value,
        body_hash,
        valid=True,
    ):
        dynamic_data = self.get_dynamic_data()
        if dynamic_data:
            dynamic_data.date_fetched = date_fetched
            dynamic_data.import_seconds = import_seconds
            dynamic_data.number_of_entries = number_of_entries

            if valid:
                dynamic_data.page_hash = hash_value
                if body_hash == "":
                    body_hash = None
                dynamic_data.body_hash = body_hash

            if valid:
                dynamic_data.consecutive_errors = 0
            else:
                dynamic_data.consecutive_errors += 1

            if dynamic_data.consecutive_errors > 20:
                id = self.id
                url = self.url
                AppLogging.notify(
                    "Disabling source ID:{} URL:{} because of errors".format(id, url)
                )
                self.enabled = False
                self.save()

            dynamic_data.save()
        else:
            consecutive_errors = 0
            if not valid:
                consecutive_errors += 1

            SourceOperationalData.objects.create(
                date_fetched=date_fetched,
                import_seconds=import_seconds,
                number_of_entries=number_of_entries,
                page_hash=hash_value,
                body_hash=body_hash,
                consecutive_errors=consecutive_errors,
                source_obj=self,
            )
        return dynamic_data

    def get_xpath_patterns(self):
        patterns = self.xpath.split(",")
        return patterns

    def is_link_ok(self, link) -> bool:
        patterns = self.get_xpath_patterns()
        for pattern in patterns:
            if re.search(pattern, link):
                return True
        return False

    def get_domain(self):
        page = UrlLocation(self.url)
        return page.get_domain()

    def get_domain_only(self):
        page = UrlLocation(self.url)
        return page.get_domain_only()

    def get_entry_url(self):
        entries = LinkDataModel.objects.filter(link=self.url)
        if entries.exists():
            return entries[0].get_absolute_url()

        else:
            return self.url

    def get_map(self):
        output_data = {}

        export_names = SourceDataController.get_export_names()
        for export_name in export_names:
            val = getattr(self, export_name)
            output_data[export_name] = val

        return output_data

    def get_map_full(self):
        return self.get_map()

    def get_full_information(data):
        from ..pluginsources.sourceurlinterface import SourceUrlInterface

        source_interface = SourceUrlInterface(data["url"])
        info = source_interface.get_props()

        if data["url"].find("http://") >= 0:
            data["url"] = data["url"].replace("http://", "https://")
            https_info = SourceUrlInterface(data["url"]).get_props()

            if "title" in info and "title" in https_info:
                if https_info["title"] and info["title"]:
                    if len(https_info["title"]) == len(info["title"]):
                        return https_info

        return info

    def get_clean_data(props):
        result = {}
        test = SourceDataController()

        for key in props:
            if hasattr(test, key):
                result[key] = props[key]

        if "url" in result and result["url"].endswith("/"):
            result["url"] = result["url"][:-1]

        return result

    def enable(self):
        if self.enabled:
            return

        op = self.get_dynamic_data()
        if op:
            op.consecutive_errors = 0
            op.save()

        entries = LinkDataModel.objects.filter(link=self.url)
        if not entries.exists():
            BackgroundJobController.source_link_add(self)

        BackgroundJobController.download_rss(self)

        self.enabled = True
        self.save()

    def disable(self):
        if not self.enabled:
            return

        from .entrywrapper import EntryWrapper

        self.enabled = False
        self.save()

        entries = LinkDataModel.objects.filter(link=self.url)
        if entries.exists():
            for entry in entries:
                w = EntryWrapper(entry=entry)
                w.evaluate()

    def edit(self, data):
        """
        TODO some iteration here?
        """
        if "url" in data:
            self.url = data["url"]
        if "title" in data:
            self.title = data["title"]
        if "category" in data:
            self.category = data["category"]
        if "subcategory" in data:
            self.subcategory = data["subcategory"]
        if "export_to_cms" in data:
            self.export_to_cms = data["export_to_cms"]
        if "remove_after_days" in data:
            self.remove_after_days = data["remove_after_days"]
        if "language" in data:
            self.language = data["language"]
        if "favicon" in data:
            self.favicon = data["favicon"]
        if "enabled" in data:
            if data["enabled"]:
                self.enable()
        if "fetch_period" in data:
            self.fetch_period = data["fetch_period"]
        if "source_type" in data:
            self.source_type = data["source_type"]
        if "proxy_location" in data:
            self.proxy_location = data["proxy_location"]

        self.save()

    def add_entry(self):
        """
        It can be used by search engine. If we add link for every source, we will be swamped
        """
        if not self.enabled:
            return

        properties = {"permament": True}
        BackgroundJobController.link_add(
            url=self.url, properties=properties, source=self
        )

    def custom_remove(self):
        entries = LinkDataModel.objects.filter(link=self.url)
        if entries.exists():
            entry = entries[0]
            entry.permament = False
            entry.save()

        jobs = BackgroundJobController.objects.filter(
            job=BackgroundJobController.JOB_PROCESS_SOURCE, subject=str(self.id)
        )
        jobs.delete()

        self.delete()

    def update_data(self, update_with=None):
        new_thumbnail = None
        if update_with:
            new_thumbnail = update_with.get_thumbnail()
        if new_thumbnail and self.favicon != new_thumbnail:
            if self.auto_update_favicon:
                self.favicon = new_thumbnail

        new_title = None
        if update_with:
            new_title = update_with.get_title()
        if new_title and self.title != new_title:
            self.title = new_title

        self.save()

        if update_with:
            data = self.get_dynamic_data()
            if data:
                data.page_hash = update_with.get_hash()
                data.body_hash = update_with.get_body_hash()
                data.save()


class SourceDataBuilder(object):
    def __init__(self, link=None, link_data=None, manual_entry=False, strict_ids=False):
        self.link = link
        self.link_data = link_data
        self.manual_entry = manual_entry
        self.strict_ids = strict_ids
        self.errors = []

        if self.link:
            self.build_from_link()

        if self.link_data:
            self.build_from_props()

    def build(self, link=None, link_data=None, manual_entry=False, strict_ids=False):

        self.link = link
        self.link_data = link_data
        self.manual_entry = manual_entry
        self.strict_ids = strict_ids

        if self.link:
            return self.build_from_link()

        if self.link_data:
            return self.build_from_props()

    def build_simple(
        self, link=None, link_data=None, manual_entry=False, strict_ids=False
    ):
        self.link = link
        link_data = link_data
        self.manual_entry = manual_entry
        self.strict_ids = strict_ids

        sources = SourceDataController.objects.filter(url=link)
        if sources.exists():
            return None

        source = SourceDataController.objects.create(link=link)

        # TODO add update job

        return source

    def build_from_link(self):
        from ..pluginurl import UrlHandler

        rss_url = self.link

        h = UrlHandler(rss_url)
        if h.is_server_error():
            self.errors.append("Url:{}. Crawling server error".format(self.link))
            return

        if not h.is_valid():
            self.errors.append("Url:{}. Link is not valid".format(self.link))
            return

        properties = h.get_properties()

        self.link_data = properties
        if not self.link_data:
            self.errors.append("Url:{}. Could not obtain data".format(self.link))
            return

        return self.build_from_props()

    def build_from_props(self, link_data=None):
        if link_data:
            self.link_data = link_data

        if "link" in self.link_data and "url" not in self.link_data:
            self.link_data["url"] = self.link_data["link"]

        if "thumbnail" in self.link_data and "favicon" not in self.link_data:
            self.link_data["favicon"] = self.link_data["thumbnail"]

        sources = SourceDataController.objects.filter(url=self.link_data["url"])
        if sources.exists():
            return None

        conf = Configuration.get_object().config_entry

        if not self.manual_entry:
            # TODO if there is no title - inherit it from 'main domain'. same goes for language.
            # maybe for thumbnail
            self.link_data["export_to_cms"] = True
            self.link_data["enabled"] = conf.default_source_state
            if "source_type" not in self.link_data:
                self.link_data["source_type"] = SourceDataModel.SOURCE_TYPE_RSS
            if "remove_after_days" not in self.link_data:
                self.link_data["remove_after_days"] = 2
            if "category_name" not in self.link_data:
                self.link_data["category_name"] = "New"
            if "subcategory_name" not in self.link_data:
                self.link_data["subcategory_name"] = "New"

        self.get_clean_data()

        source = self.add_internal()
        # domains are created when entry is created
        if not source:
            return None

        # SourceDataController.fix_entries(source)
        # background jobs to reconnect entries

        self.add_to_download(source)

        return source

    def add_internal(self):
        """
        Category and subcategory names can be empty, then objects are not set
        """
        source = None

        if "language" not in self.link_data or self.link_data["language"] is None:
            self.link_data["language"] = ""

        source = SourceDataController.objects.create(**self.link_data)

        # TODO add entry in source update job (or change link update job)

        return source

    def get_clean_data(self):
        result = {}
        props = self.link_data
        test = SourceDataController()

        for key in props:
            if hasattr(test, key):
                result[key] = props[key]

        self.link_data = result

        return result

    def add_to_download(self, source):
        if source.enabled:
            BackgroundJobController.download_rss(source)

        BackgroundJobController.source_link_add(source)
