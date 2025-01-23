from ..webtools import (
    HtmlPage,
    RssPage,
    JsonPage,
    HttpPageHandler,
    UrlLocation,
)
from utils.services import OpenRss

from ..models import (
    SourceDataModel,
)
from ..configuration import Configuration
from ..pluginsources.sourceparseplugin import BaseParsePlugin
from ..pluginurl.urlhandler import UrlHandler, UrlHandlerEx


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

        url_ex = UrlHandlerEx(self.url)

        all_properties = url_ex.get_properties()

        if all_properties:
            properties = url_ex.get_section("Properties")
            response = url_ex.get_section("Response")

            if properties:
                props = {}
                if "feed_0" in properties:
                    props["url"] = properties["feed_0"]
                else:
                    props["url"] = url_ex.url
                props["title"] = properties["title"]
                props["description"] = properties["description"]
                props["language"] = properties["language"]
                props["favicon"] = properties["thumbnail"]
                props["status_code"] = response["status_code"]

                props["source_type"] = SourceDataModel.SOURCE_TYPE_RSS
                if "Content-Type":
                    content_type = response["Content-Type"]
                    if content_type.find("html") >= 1:
                        props["source_type"] = SourceDataModel.SOURCE_TYPE_PARSE
                    if content_type.find("json") >= 1:
                        props["source_type"] = SourceDataModel.SOURCE_TYPE_JSON
        else:
            props = {}

        if "remove_after_days" not in props:
            props["remove_after_days"] = 0
        if "fetch_period" not in props:
            props["fetch_period"] = "3600"
        if "age" not in props:
            props["age"] = 0
        if "status_code" not in props:
            if self.u:
                props["status_code"] = self.u.get_status_code()
        if "language" not in props or props["language"] is None:
            props["language"] = ""
        if "category_name" not in props or props["category_name"] is None:
            props["category_name"] = "New"
        if "subcategory_name" not in props or props["subcategory_name"] is None:
            props["subcategory_name"] = "New"

        return props

    def is_property_set(self, input_props, property):
        return property in input_props and input_props[property]
