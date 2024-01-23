from ..webtools import BasePage, HtmlPage, RssPage, Url, JsonPage
from ..models import (
    SourceDataModel,
)
from ..pluginsources.sourceparseplugin import BaseParsePlugin
from ..pluginentries.urlhandler import UrlHandler


class SourceUrlInterface(object):
    """
    Provides interface between Source and URL Properties
    """

    def __init__(self, url):
        self.url = url

        if self.url.endswith("/"):
            self.url = self.url[:-1]

    def get_props(self, input_props=None, use_selenium=False):
        fast_check = False

        p = UrlHandler.get(self.url, fast_check=fast_check, use_selenium=use_selenium)

        if p.is_rss(fast_check=fast_check):
            return self.get_props_from_rss(self.url, p)
        elif p.is_youtube():
            # Someone might be surprised that added URL is being replaced

            handler = UrlHandler.get(self.url)
            p = RssPage(handler.get_channel_feed_url())

            return self.get_props_from_rss(p.url, p)
        elif p.is_html(fast_check=fast_check) and p.get_rss_url():
            # Someone might be surprised that added URL is being replaced
            p = RssPage(p.get_rss_url())
            return self.get_props_from_rss(p.url, p)
        elif JsonPage(p.url, p.get_contents()).is_json():
            return self.get_props_from_json(p.url, p)
        else:
            return self.get_props_from_page(p)

    def get_props_from_rss(self, url, p):
        data = {}
        data["url"] = url
        data["source_type"] = SourceDataModel.SOURCE_TYPE_RSS
        title = p.get_title()
        if title:
            data["title"] = title
        description = p.get_description()
        if description:
            data["description"] = description
        language = p.get_language()
        if language:
            data["language"] = language
        thumb = p.get_thumbnail()
        if thumb:
            data["favicon"] = thumb
        return data

    def get_props_from_json(self, url, p):
        j = JsonPage(p.url, p.get_contents())

        if "source" in j.json_obj:
            return self.get_props_from_json_source(url, p, j)

        elif "sources" in j.json_obj:
            return self.get_props_from_json_sources(url, p, j)

        else:
            return self.get_props_from_page(p)

    def get_props_from_json_source(self, url, p, j):
        source_obj = j.json_obj["source"]

        data = {}
        data["source_type"] = SourceDataModel.SOURCE_TYPE_JSON
        data["proxy_location"] = url
        data["url"] = url
        if "title" in source_obj:
            data["title"] = source_obj["title"] + " - Proxy"
        if "description" in source_obj:
            data["description"] = source_obj["description"]
        if "category" in source_obj:
            data["category"] = source_obj["category"]
        if "subcategory" in source_obj:
            data["subcategory"] = source_obj["subcategory"]
        if "language" in source_obj:
            data["language"] = source_obj["language"]
        if "favicon" in source_obj:
            data["favicon"] = source_obj["favicon"]

        return data

    def get_props_from_json_sources(self, url, p, j):
        source_obj = j.json_obj["sources"]

        data = {}
        data["source_type"] = SourceDataModel.SOURCE_TYPE_JSON
        data["proxy_location"] = url
        data["url"] = url
        data["title"] = "Instance Proxy"

        return data

    def get_props_from_page(self, p):
        data = {}
        data["url"] = p.url
        data["source_type"] = BaseParsePlugin.PLUGIN_NAME
        data["title"] = p.get_title()
        data["description"] = p.get_title()
        data["language"] = p.get_language()
        data["page_rating"] = p.get_page_rating()
        return data
