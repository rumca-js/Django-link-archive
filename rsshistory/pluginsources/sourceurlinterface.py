from ..webtools import HtmlPage, RssPage, Url, JsonPage, PageOptions
from ..models import (
    SourceDataModel,
)
from ..pluginsources.sourceparseplugin import BaseParsePlugin
from ..pluginurl.urlhandler import UrlHandler


class SourceUrlInterface(object):
    """
    Provides interface between Source and URL Properties
    """

    def __init__(self, url, fast_check=True, use_selenium=False):
        self.url = UrlHandler.get_cleaned_link(url)

        options = PageOptions()
        options.fast_parsing = fast_check
        options.use_selenium_headless = use_selenium

        self.h = UrlHandler(self.url, page_options=options)
        if self.h.response:
            self.url = self.h.response.url

        self.p = self.h.p

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

        return props

    def get_props_internal(self, input_props=None):
        p = self.p

        if type(p) is RssPage or type(p) is UrlHandler.youtube_channel_handler:
            return self.get_props_from_rss(input_props)
        elif type(p) is UrlHandler.youtube_video_handler:
            # Someone might be surprised that added URL is being replaced

            self.h = UrlHandler(p.get_channel_feed_url())
            self.p = self.h.p

            return self.get_props_from_rss(input_props)
        elif type(p) is HtmlPage and p.get_rss_url():
            # Someone might be surprised that added URL is being replaced
            h = UrlHandler(h.p.get_rss_url())
            return self.get_props_from_rss(input_props)
        elif type(p) is JsonPage:
            return self.get_props_from_json(input_props)
        else:
            return self.get_props_from_page(input_props)

    def get_props_from_rss(self, input_props=None):
        p = self.p
        url = self.url

        input_props["url"] = self.url

        if type(p) is UrlHandler.youtube_channel_handler:
            input_props["source_type"] = SourceDataModel.SOURCE_TYPE_YOUTUBE
        else:
            input_props["source_type"] = SourceDataModel.SOURCE_TYPE_RSS

        title = p.get_title()
        print("title: {}".format(title))
        if title:
            input_props["title"] = title
        description = p.get_description()
        if description:
            input_props["description"] = description
        language = p.get_language()
        if language:
            input_props["language"] = language
        thumb = p.get_thumbnail()
        if thumb:
            input_props["favicon"] = thumb
        return input_props

    def get_props_from_json(self, input_props):
        p = self.p

        j = JsonPage(p.url, p.get_contents())

        if "source" in j.json_obj:
            return self.get_props_from_json_source(input_props, j)

        elif "sources" in j.json_obj:
            return self.get_props_from_json_sources(input_props, j)

        else:
            input_props = self.get_props_from_page(p)
            input_props["source_type"] = SourceDataModel.SOURCE_TYPE_JSON
            return input_props

    def get_props_from_json_source(self, input_props, j):
        p = self.p
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
        p = self.p

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
