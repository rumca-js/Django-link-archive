from datetime import datetime, date, timedelta
import os
import traceback

from django.db import models
from django.urls import reverse
from django.db.models import Q

from ..models import (
    LinkDataModel,
    PersistentInfo,
    SourceDataModel,
    SourceOperationalData,
    SourceCategories,
    SourceSubCategories,
)

from ..configuration import Configuration
from ..webtools import BasePage, HtmlPage, RssPage, Url
from ..apps import LinkDatabase
from ..dateutils import DateUtils


class SourceDataController(SourceDataModel):
    class Meta:
        proxy = True

    def get_absolute_url(self):
        """Returns the URL to access a particular author instance."""
        return reverse(
            "{}:source-detail".format(LinkDatabase.name), args=[str(self.id)]
        )

    def cleanup():
        SourceDataModel.reset_dynamic_data()

    def get_days_to_remove(self):
        days = 0
        try:
            days = int(self.remove_after_days)
        except Exception as E:
            PersistentInfo.error("Exception {}".format(str(E)))

        return days

    def get_long_description(self):
        return "Category:{} Subcategory:{} Export:{} On Hold:{} Type:{}".format(
            self.category,
            self.subcategory,
            self.export_to_cms,
            self.on_hold,
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
        if self.on_hold:
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
        days = self.get_days_to_remove()

        if days > 0:
            return True
        else:
            return False

    def get_op_data(self):
        if hasattr(self, "dynamic_data"):
            return self.dynamic_data

    def get_date_fetched(self):
        obj = self.get_op_data()
        if obj:
            return obj.date_fetched

    def get_page_hash(self):
        obj = self.get_op_data()
        if obj:
            return obj.page_hash

    def get_import_seconds(self):
        obj = self.get_op_data()
        if obj:
            return obj.import_seconds

    def get_number_of_entries(self):
        obj = self.get_op_data()
        if obj:
            return obj.number_of_entries

    def set_operational_info(
        self, date_fetched, number_of_entries, import_seconds, hash_value, valid=True
    ):
        obj = self.get_op_data()
        if obj:
            obj.date_fetched = date_fetched
            obj.import_seconds = import_seconds
            obj.number_of_entries = number_of_entries

            if valid:
                obj.page_hash = hash_value

            if valid:
                obj.consecutive_errors = 0
            else:
                obj.consecutive_errors += 0

            obj.save()
        else:
            # previously we could have dangling data without relation
            op_datas = SourceOperationalData.objects.filter(url=self.url)

            consecutive_errors = 0
            if not valid:
                consecutive_errors += 1

            if op_datas.count() == 0:
                SourceOperationalData.objects.create(
                    url=self.url,
                    date_fetched=date_fetched,
                    import_seconds=import_seconds,
                    number_of_entries=number_of_entries,
                    page_hash=hash_value,
                    consecutive_errors = consecutive_errors,
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

    def get_favicon(self):
        if self.favicon:
            return self.favicon

        # returning real favicon from HTML is too long
        return BasePage(self.url).get_domain() + "/favicon.ico"

    def get_domain(self):
        page = BasePage(self.url)
        return page.get_domain()

    def get_domain_only(self):
        page = BasePage(self.url)
        return page.get_domain_only()

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
            "favicon",
            "on_hold",
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
            "favicon",
            "on_hold",
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

    def get_channel_page_url(self):
        from ..pluginentries.handlerchannel import ChannelHandler

        handler = ChannelHandler.get(self.url)

        return handler.get_channel_url()

    def is_channel_page_url(self):
        from ..pluginentries.handlerchannel import ChannelHandler

        return ChannelHandler.get_supported(self.url)

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
        if self.on_hold:
            from .backgroundjob import BackgroundJobController

            op = source.get_op_data()
            if op:
                op.consecutive_errors = 0
                op.save()

            BackgroundJobController.download_rss(self)

            self.on_hold = False
            self.save()

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
        if "on_hold" in data:
            if not data["on_hold"]:
                self.enable()
        if "fetch_period" in data:
            self.fetch_period = data["fetch_period"]
        if "source_type" in data:
            self.source_type = data["source_type"]
        if "proxy_location" in data:
            self.proxy_location = data["proxy_location"]

        self.save()


class SourceDataBuilder(object):
    def __init__(self, link=None, link_data=None, manual_entry = False):
        self.link = link
        self.link_data = link_data
        self.manual_entry = manual_entry

        if self.link:
            self.add_from_link()

        if self.link_data:
            self.add_from_props()

    def add_from_link(self):
        rss_url = self.link

        if rss_url.endswith("/"):
            rss_url = rss_url[:-1]

        page = RssPage(rss_url)
        if not page.is_valid():
            return

        self.link_data = page.get_properties()

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
            self.link_data["on_hold"] = not conf.auto_store_sources_enabled
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
        try:
            # TODO add domain when adding new source
            source = SourceDataController.objects.create(**self.link_data)
            return source
        except Exception as E:
            LinkDatabase.error("Exception:{}".format(str(E)))
            PersistentInfo.error("Exception {}".format(str(E)))

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
            subcategory_object = SourceSubCategories.add(category_name, subcategory_name)

        # self.link_data["category_object"] = category_object
        # self.link_data["subcategory_object"] = subcategory_object

    def add_domains(self):
        if Configuration.get_object().config_entry.auto_store_domain_info:
            from .entries import LinkDataBuilder

            p = BasePage(self.link_data["url"])
            LinkDataBuilder(link=p.get_domain())

    def add_to_download(self, source):
        if not source.on_hold:
            from .backgroundjob import BackgroundJobController

            BackgroundJobController.download_rss(source)
