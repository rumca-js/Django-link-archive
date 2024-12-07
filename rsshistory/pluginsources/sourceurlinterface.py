from ..webtools import HtmlPage, RssPage, JsonPage, HttpPageHandler, UrlLocation
from utils.services import OpenRss

from ..models import (
    SourceDataModel,
)
from ..pluginsources.sourceparseplugin import BaseParsePlugin
from ..pluginurl.urlhandler import UrlHandler


class SourceUrlInterface(object):
    """
    Provides interface between Source and URL Properties
    """

    def __init__(self, url, use_headless_browser=False):
        self.url = UrlHandler.get_cleaned_link(url)
        self.use_headless_browser = use_headless_browser

    def get_props(self, input_props=None):
        if not input_props:
            input_props = {}

        props = self.get_props_internal(input_props)

        if "remove_after_days" not in props:
            props["remove_after_days"] = 0
        if "fetch_period" not in props:
            props["fetch_period"] = "3600"
        if "age" not in props:
            props["age"] = 0
        if "status_code" not in props:
            props["status_code"] = self.u.get_status_code()
        if "language" not in props or props["language"] is None:
            props["language"] = ""
        if "category_name" not in props or props["category_name"] is None:
            props["category_name"] = "New"
        if "subcategory_name" not in props or props["subcategory_name"] is None:
            props["subcategory_name"] = "New"

        return props

    def get_props_internal(self, input_props=None):
        url_object = UrlHandler(self.url)

        url = UrlHandler.find_rss_url(url_object)
        if url:
            url.get_response()

            feeds = url.get_feeds()
            if feeds and len(feeds) > 0:
                self.url = feeds[0]
            else:
                self.url = url.url
            self.u = url
            return self.get_props_from_rss(input_props)
        else:
            rss = OpenRss(self.url)
            link = rss.find_rss_link()
            if link:
                if self.url != link:
                    url = UrlHandler(link)
                    url.get_response()

                    self.url = link
                    self.u = url
                    return self.get_props_from_rss(input_props)

            if url_object:
                self.url = url_object.url
                self.u = url_object

                handler = self.u.get_handler()

                if type(handler) is HttpPageHandler:
                    if type(handler.p) is JsonPage:
                        return self.get_props_from_json(input_props)

        return self.get_props_from_page(input_props)

    def get_props_from_rss(self, input_props=None):
        u = self.u
        handler = self.u.get_handler()
        url = self.url

        input_props["url"] = self.url

        if type(handler) is UrlHandler.youtube_channel_handler:
            input_props["source_type"] = SourceDataModel.SOURCE_TYPE_YOUTUBE
        else:
            input_props["source_type"] = SourceDataModel.SOURCE_TYPE_RSS

        title = u.get_title()
        if title:
            input_props["title"] = title
        description = u.get_description()
        if description:
            input_props["description"] = description
        language = u.get_language()
        if language:
            input_props["language"] = language
        thumb = u.get_thumbnail()
        if thumb:
            input_props["favicon"] = thumb
        return input_props

    def get_props_from_json(self, input_props):
        u = self.u

        j = JsonPage(u.url, u.get_contents())

        if "source" in j.json_obj:
            return self.get_props_from_json_source(input_props, j)

        elif "sources" in j.json_obj:
            return self.get_props_from_json_sources(input_props, j)

        else:
            input_props = self.get_props_from_page(p)
            input_props["source_type"] = SourceDataModel.SOURCE_TYPE_JSON
            return input_props

    def get_props_from_json_source(self, input_props, j):
        url = self.url

        source_obj = j.json_obj["source"]

        input_props["source_type"] = SourceDataModel.SOURCE_TYPE_JSON
        input_props["proxy_location"] = url
        input_props["url"] = url
        if "title" in source_obj:
            input_props["title"] = source_obj["title"] + " - Proxy"
        if "description" in source_obj:
            input_props["description"] = source_obj["description"]
        if "category_name" in source_obj:
            input_props["category_name"] = source_obj["category_name"]
        if "subcategory_name" in source_obj:
            input_props["subcategory_name"] = source_obj["subcategory_name"]
        if "language" in source_obj:
            input_props["language"] = source_obj["language"]
        if "favicon" in source_obj:
            input_props["favicon"] = source_obj["favicon"]

        return input_props

    def get_props_from_json_sources(self, input_props, j):
        source_obj = j.json_obj["sources"]
        url = self.url

        input_props["source_type"] = SourceDataModel.SOURCE_TYPE_JSON
        input_props["proxy_location"] = url
        input_props["url"] = url
        input_props["title"] = "Instance Proxy"

        return input_props

    def get_props_from_page(self, input_props):
        p = self.u

        input_props["url"] = p.url
        # if we do not know what to do with it, we can always collect links from within
        input_props["source_type"] = BaseParsePlugin.PLUGIN_NAME
        input_props["title"] = p.get_title()
        input_props["description"] = p.get_title()
        input_props["language"] = p.get_language()
        input_props["page_rating"] = p.get_page_rating()
        return input_props

    def is_property_set(self, input_props, property):
        return property in input_props and input_props[property]

    def is_reddit_channel(self):
        p = UrlLocation(self.url)
        if p.get_domain_only().find("reddit.com") >= 0:
            parts = p.split()
            if len(parts) == 5 and parts[3] == "r":
                return True

        return False

    def get_reddit_rss(self):
        if self.url.endswith("/"):
            return self.url + ".rss"
        else:
            return self.url + "/.rss"

    def get_reddit_channel_name(self):
        p = UrlLocation(self.url)
        parts = p.split()
        return parts[4]
