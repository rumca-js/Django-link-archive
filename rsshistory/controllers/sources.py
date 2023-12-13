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
)

from ..configuration import Configuration
from ..webtools import BasePage, HtmlPage, RssPage
from ..apps import LinkDatabase


class SourceDataController(SourceDataModel):
    class Meta:
        proxy = True

    def add(source_data_map):
        sources = SourceDataController.objects.filter(url=source_data_map["url"])
        if sources.count() > 0:
            return None

        # TODO add domain when adding new source
        source = SourceDataController.objects.create(**source_data_map)

        SourceDataController.fix_entries(source)

        if Configuration.get_object().config_entry.auto_store_domain_info:
            from .entries import LinkDataHyperController

            p = BasePage(source_data_map["url"])
            LinkDataHyperController.add_simple(p.get_domain())

        return source

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
        from ..dateutils import DateUtils

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

        page = BasePage(self.url)
        domain = page.get_domain()
        return domain + "/favicon.ico"

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
        p = HtmlPage(data["url"])
        # TODO if passed url is youtube video, obtain information, obtain channel feed url

        if p.is_rss():
            return SourceDataController.get_info_from_rss(data["url"])
        elif p.is_youtube():
            from ..pluginentries.handlervideoyoutube import YouTubeVideoHandler

            handler = YouTubeVideoHandler(data["url"])
            handler.download_details()
            return SourceDataController.get_info_from_rss(
                handler.get_channel_feed_url()
            )
        elif p.get_rss_url():
            p = HtmlPage(data["url"])
            return SourceDataController.get_info_from_rss(p.get_rss_url())
        else:
            return SourceDataController.get_info_from_page(data["url"], p)

    def get_info_from_rss(url):
        reader = RssPage(url)
        feed = reader.parse()

        data = {}
        data["url"] = url
        data["source_type"] = SourceDataModel.SOURCE_TYPE_RSS
        title = reader.get_title()
        if title:
            data["title"] = title
        description = reader.get_description()
        if description:
            data["description"] = description
        language = reader.get_language()
        if language:
            data["language"] = language
        thumb = reader.get_thumbnail()
        if thumb:
            data["favicon"] = thumb
        return data

    def get_info_from_page(url, p):
        from ..pluginsources.sourceparseplugin import BaseParsePlugin

        data = {}
        data["url"] = url
        data["source_type"] = BaseParsePlugin.PLUGIN_NAME
        data["language"] = p.get_language()
        data["title"] = p.get_title()
        data["description"] = p.get_title()
        data["page_rating"] = p.get_page_rating()
        return data

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
