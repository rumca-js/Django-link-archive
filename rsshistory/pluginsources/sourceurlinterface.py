from ..models import (
    SourceDataModel,
)
from ..pluginsources.sourceparseplugin import BaseParsePlugin
from ..pluginurl.urlhandler import UrlHandler
from ..webtools import HtmlPage, RssPage, JsonPage, InternetPageHandler, DomainAwarePage


class SourceUrlInterface(object):
    """
    Provides interface between Source and URL Properties
    """

    def __init__(self, url, fast_check=True, use_headless_browser=False):
        self.url = UrlHandler.get_cleaned_link(url)
        self.fast_check = fast_check
        self.use_headless_browser = use_headless_browser

    def get_props(self, input_props=None):
        options = UrlHandler(self.url).get_init_page_options()
        options.fast_parsing = self.fast_check
        options.use_headless_browser = self.use_headless_browser

        self.u = UrlHandler(self.url, page_options=options)
        self.response = self.u.get_response()

        if self.u.response:
            self.url = self.u.response.url

        if not input_props:
            input_props = {}

        if self.u is None:
            return input_props

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

        return props

    def get_props_internal(self, input_props=None):
        handler = self.u.get_handler()

        if type(handler) is UrlHandler.youtube_channel_handler:
            return self.get_props_from_rss(input_props)
        elif type(handler) is UrlHandler.youtube_video_handler:
            # Someone might be surprised that added URL is being replaced
            self.url = handler.get_channel_feed_url()
            self.u = UrlHandler(self.url)
            self.u.get_response()

            return self.get_props_from_rss(input_props)
        elif type(handler) is InternetPageHandler:
            if self.is_reddit_channel():
                rss = self.get_reddit_rss()
                if not rss:
                    return self.get_props_from_page(input_props)

                self.url = rss
                handler = UrlHandler(self.url)
                self.u = handler
                self.u.get_response()

                return self.get_props_internal(input_props)

            elif type(handler.p) is RssPage:
                return self.get_props_from_rss(input_props)
            elif type(handler.p) is HtmlPage and handler.p.get_rss_url():
                # Someone might be surprised that added URL is being replaced
                url = handler.p.get_rss_url()
                if not url:
                    return self.get_props_from_page(input_props)

                self.url = url
                handler = UrlHandler(url)
                self.u = handler
                self.u.get_response()

                return self.get_props_internal(input_props)
            elif type(handler.p) is JsonPage:
                return self.get_props_from_json(input_props)
            else:
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
        if "category" in source_obj:
            input_props["category"] = source_obj["category"]
        if "subcategory" in source_obj:
            input_props["subcategory"] = source_obj["subcategory"]
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
        p = DomainAwarePage(self.url)
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
        p = DomainAwarePage(self.url)
        parts = p.split()
        return parts[4]
