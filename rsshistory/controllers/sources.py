from datetime import datetime, date, timedelta
import os
import traceback

from django.db import models
from django.urls import reverse
from django.db.models import Q

from ..models import (
    LinkDataModel,
    AppLogging,
    SourceDataModel,
    SourceOperationalData,
    SourceCategories,
    SourceSubCategories,
)

from ..configuration import Configuration
from ..webtools import HtmlPage, RssPage, Url, DomainAwarePage
from ..apps import LinkDatabase
from ..dateutils import DateUtils


class SourceDataController(SourceDataModel):
    class Meta:
        proxy = True

    def cleanup():
        SourceDataModel.reset_dynamic_data()

        sources = SourceDataModel.objects.filter(enabled=True)

        for source in sources:
            entries = LinkDataModel.objects.filter(link=source.url)
            if entries.count() == 0:
                SourceDataController.add_entry(source)
            else:
                entry = entries[0]
                entry.permanent = True
                entry.save()

    def get_days_to_remove(self):
        days = self.remove_after_days
        return days

    def get_long_description(self):
        return "Category:{} Subcategory:{} Export:{} Enabled:{} Type:{}".format(
            self.category,
            self.subcategory,
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

    def is_removeable(self):
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

    def get_import_seconds(self):
        obj = self.get_dynamic_data()
        if obj:
            return obj.import_seconds

    def get_number_of_entries(self):
        obj = self.get_dynamic_data()
        if obj:
            return obj.number_of_entries

    def set_operational_info(
        self, date_fetched, number_of_entries, import_seconds, hash_value, valid=True
    ):
        obj = self.get_dynamic_data()
        if obj:
            obj.date_fetched = date_fetched
            obj.import_seconds = import_seconds
            obj.number_of_entries = number_of_entries

            if valid:
                obj.page_hash = hash_value

            if valid:
                obj.consecutive_errors = 0
            else:
                obj.consecutive_errors += 1

            obj.save()
        else:
            # previously we could have dangling data without relation
            op_datas = SourceOperationalData.objects.filter(source_obj=self)

            consecutive_errors = 0
            if not valid:
                consecutive_errors += 1

            if op_datas.count() == 0:
                SourceOperationalData.objects.create(
                    date_fetched=date_fetched,
                    import_seconds=import_seconds,
                    number_of_entries=number_of_entries,
                    page_hash=hash_value,
                    consecutive_errors=consecutive_errors,
                    source_obj=self,
                )
            else:
                obj = op_datas[0]
                obj.date_fetched = date_fetched
                obj.import_seconds = import_seconds
                obj.number_of_entries = number_of_entries
                obj.source_obj = self

                if valid:
                    obj.page_hash = hash_value

                if valid:
                    obj.consecutive_errors = 0
                else:
                    obj.consecutive_errors += 0

                obj.save()

        return obj

    def get_domain(self):
        page = DomainAwarePage(self.url)
        return page.get_domain()

    def get_domain_only(self):
        page = DomainAwarePage(self.url)
        return page.get_domain_only()

    def get_entry_url(self):
        entries = LinkDataModel.objects.filter(link=self.url)
        if entries.count() > 0:
            return entries[0].get_absolute_url()

        else:
            return self.url

    def get_export_names():
        return [
            "id",
            "url",
            "title",
            "category",
            "subcategory",
            "dead",
            "export_to_cms",
            "remove_after_days",
            "language",
            "age",
            "favicon",
            "enabled",
            "fetch_period",
            "source_type",
            "proxy_location",
        ]

    def get_query_names():
        return [
            "id",
            "url",
            "title",
            "category",
            "subcategory",
            "dead",
            "export_to_cms",
            "remove_after_days",
            "language",
            "age",
            "favicon",
            "enabled",
            "fetch_period",
            "source_type",
            "proxy_location",
        ]

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

        info = SourceUrlInterface(data["url"]).get_props()

        if data["url"].find("http://") >= 0:
            data["url"] = data["url"].replace("http://", "https://")
            https_info = SourceUrlInterface(data["url"]).get_props()

            if "title" in info and "title" in https_info:
                if len(https_info["title"]) == len(info["title"]):
                    return https_info

        return info

    def fix_entries(self):
        entries = LinkDataModel.objects.filter(source=self.url)
        for entry in entries:
            entry.source_obj = self
            entry.save()

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

        from .backgroundjob import BackgroundJobController

        op = self.get_dynamic_data()
        if op:
            op.consecutive_errors = 0
            op.save()

        entries = LinkDataModel.objects.filter(link=self.url)
        if entries.count() == 0:
            SourceDataController.add_entry(self)

        BackgroundJobController.download_rss(self)

        self.enabled = True
        self.save()

    def disable(self):
        if not self.enabled:
            return

        from .backgroundjob import BackgroundJobController
        from .entriesutils import EntryWrapper

        self.enabled = False
        self.save()

        entries = LinkDataModel.objects.filter(link=self.url)
        if entries.count() > 0:
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
        if "dead" in data:
            self.dead = data["dead"]
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

    def add_entry(source):
        """
        It can be used by search engine. If we add link for every source, we will be swamped
        """
        if not source:
            return

        if not source.enabled:
            return

        from .backgroundjob import BackgroundJobController

        properties = {"permament": True}
        BackgroundJobController.link_add(
            url=source.url, properties=properties, source=source
        )

    def custom_remove(self):
        entries = LinkDataModel.objects.filter(link=self.url)
        if entries.exists():
            entry = entries[0]
            entry.permament = False

        self.delete()


class SourceDataBuilder(object):
    def __init__(self, link=None, link_data=None, manual_entry=False):
        self.link = link
        self.link_data = link_data
        self.manual_entry = manual_entry

        if self.link:
            self.add_from_link()

        if self.link_data:
            self.add_from_props()

    def add_from_link(self):
        from ..pluginurl import UrlHandler

        rss_url = self.link

        if rss_url.endswith("/"):
            rss_url = rss_url[:-1]

        h = UrlHandler(rss_url)
        if not h.is_valid():
            return

        self.link_data = h.get_properties()

        return self.add_from_props()

    def add_from_props(self):
        if "link" in self.link_data and "url" not in self.link_data:
            self.link_data["url"] = self.link_data["link"]

        if "thumbnail" in self.link_data and "favicon" not in self.link_data:
            self.link_data["favicon"] = self.link_data["thumbnail"]

        sources = SourceDataController.objects.filter(url=self.link_data["url"])
        if sources.count() > 0:
            return None

        self.add_categories()

        conf = Configuration.get_object().config_entry

        if not self.manual_entry:
            # TODO if there is no title - inherit it from 'main domain'. same goes for language.
            # maybe for thumbnail
            self.link_data["export_to_cms"] = True
            self.link_data["enabled"] = conf.new_source_enabled_state
            self.link_data["source_type"] = SourceDataModel.SOURCE_TYPE_RSS
            self.link_data["remove_after_days"] = 2
            self.link_data["category"] = "New"
            self.link_data["subcategory"] = "New"

        self.get_clean_data()

        source = self.add_internal()
        if not source:
            return None

        SourceDataController.fix_entries(source)

        self.add_domains()
        self.add_to_download(source)

        return source

    def add_internal(self):
        """
        Category and subcategory names can be empty, then objects are not set
        """
        source = None

        if "language" not in self.link_data or self.link_data["language"] is None:
            self.link_data["language"] = ""

        try:
            source = SourceDataController.objects.create(**self.link_data)
        except Exception as E:
            AppLogging.exc(E, "Cannot create source:{}\n{}".format(self.link_data))

        self.additional_source_operations(source)

        return source

    def additional_source_operations(self, source):
        from .backgroundjob import BackgroundJobController

        if source:
            SourceDataController.add_entry(source)
            BackgroundJobController.download_file(source.favicon)

    def get_clean_data(self):
        result = {}
        props = self.link_data
        test = SourceDataController()

        for key in props:
            if hasattr(test, key):
                result[key] = props[key]

        self.link_data = result

        return result

    def add_categories(self):
        category_name = None
        subcategory_name = None

        if "category" in self.link_data:
            category_name = self.link_data["category"]
        if "subcategory" in self.link_data:
            subcategory_name = self.link_data["subcategory"]

        if category_name:
            category_object = SourceCategories.add(category_name)
        if category_name and subcategory_name:
            subcategory_object = SourceSubCategories.add(
                category_name, subcategory_name
            )

        # self.link_data["category_object"] = category_object
        # self.link_data["subcategory_object"] = subcategory_object

    def add_domains(self):
        if Configuration.get_object().config_entry.enable_domain_support:
            from .entriesutils import EntryDataBuilder

            p = DomainAwarePage(self.link_data["url"])
            EntryDataBuilder(link=p.get_domain())

    def add_to_download(self, source):
        if source.enabled:
            from .backgroundjob import BackgroundJobController

            BackgroundJobController.download_rss(source)
