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
        self, date_fetched, number_of_entries, import_seconds, hash_value
    ):
        obj = self.get_op_data()
        if obj:
            obj.date_fetched = date_fetched
            obj.import_seconds = import_seconds
            obj.number_of_entries = number_of_entries
            obj.page_hash = hash_value
            obj.save()
        else:
            # previously we could have dangling data without relation
            op_datas = SourceOperationalData.objects.filter(url=self.url)

            if op_datas.count() == 0:
                SourceOperationalData.objects.create(
                    url=self.url,
                    date_fetched=date_fetched,
                    import_seconds=import_seconds,
                    number_of_entries=number_of_entries,
                    page_hash=hash_value,
                    source_obj=self,
                )
            else:
                obj = op_datas[0]
                obj.date_fetched = date_fetched
                obj.import_seconds = import_seconds
                obj.number_of_entries = number_of_entries
                obj.page_hash = hash_value
                obj.source_obj = self
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


class SourceDataBuilder(object):
    def __init__(self, link=None, link_data=None):
        self.link = link
        self.link_data = link_data

        if self.link:
            self.add_from_link()

        if self.link_data:
            self.add_from_props()

    def add_from_link(self):
        rss_url = self.link

        conf = Configuration.get_object().config_entry

        if rss_url.endswith("/"):
            rss_url = rss_url[:-1]

        if SourceDataModel.objects.filter(url=rss_url).count() > 0:
            return

        if "contents" in self.link_data:
            parser = RssPage(rss_url, self.link_data["contents"])
        else:
            parser = RssPage(rss_url)

        d = parser.parse()
        if d is None:
            PersistentInfo.error("RSS is empty: rss_url:{0}".format(rss_url))
            return

        if len(d.entries) == 0:
            PersistentInfo.error("RSS no entries: rss_url:{0}".format(rss_url))
            return

        props = {}
        props["url"] = rss_url

        title = parser.get_title()
        if title:
            props["title"] = title
        if not title:
            props["title"] = self.link_data["title"]

        props["export_to_cms"] = True
        language = parser.get_language()
        if language:
            props["language"] = language
        thumbnail = parser.get_thumbnail()
        if thumbnail:
            props["favicon"] = thumbnail
        props["on_hold"] = not conf.auto_store_sources_enabled
        props["source_type"] = SourceDataModel.SOURCE_TYPE_RSS
        props["remove_after_days"] = 2

        props["category"] = "New"
        props["subcategory"] = "New"

        self.add_from_props(props)

    def add_from_props(self):
        sources = SourceDataController.objects.filter(url=self.link_data["url"])
        if sources.count() > 0:
            return None

        self.add_categories()

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

    def add_categories(self):
        category_name = self.link_data["category"]
        subcategory_name = self.link_data["subcategory"]

        category_object = SourceCategories.add(category_name)
        subcategory_object = SourceSubCategories.add(category_name, subcategory_name)

        #self.link_data["category_object"] = category_object
        #self.link_data["subcategory_object"] = subcategory_object

    def add_domains(self):
        if Configuration.get_object().config_entry.auto_store_domain_info:
            from .entries import LinkDataBuilder

            p = BasePage(self.link_data["url"])
            LinkDataBuilder(link=p.get_domain())

    def add_to_download(self, source):
        if not source.on_hold:
            from .backgroundjob import BackgroundJobController

            BackgroundJobController.download_rss(source)
