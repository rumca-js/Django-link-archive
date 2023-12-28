from ..webtools import BasePage, HtmlPage, RssPage, Url
from ..models import (
    SourceDataModel,
)


class SourceUrlInterface(object):
    """
    Provides interface between Source and URL Properties
    """

    def __init__(self, url):
        self.url = url

        if self.url.endswith("/"):
            self.url = self.url[:-1]

    def get_props(self, input_props=None):
        p = Url.get(self.url)

        if p.is_rss():
            return self.get_props_from_rss(self.url, p)
        elif p.is_youtube():
            # Someone might be surprised that added URL is being replaced
            from ..pluginentries.entryurlinterface import UrlHandler

            handler = UrlHandler.get(self.url)
            handler.download_details()

            p = RssPage(handler.get_channel_feed_url())

            return self.get_props_from_rss(p.url, p)
        elif p.is_html() and p.get_rss_url():
            # Someone might be surprised that added URL is being replaced
            p = RssPage(p.get_rss_url())
            return self.get_props_from_rss(p.url, p)
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

    def get_props_from_page(self, p):
        from ..pluginsources.sourceparseplugin import BaseParsePlugin

        data = {}
        data["url"] = self.url
        data["source_type"] = BaseParsePlugin.PLUGIN_NAME
        data["language"] = p.get_language()
        data["title"] = p.get_title()
        data["description"] = p.get_title()
        data["page_rating"] = p.get_page_rating()
        return data
