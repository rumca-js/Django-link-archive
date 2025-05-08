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
from ..pluginurl.urlhandler import UrlHandlerEx


class SourceUrlInterface(object):
    """
    Provides interface between Source and URL Properties
    """

    def __init__(self, url, browser=None):
        self.url = UrlHandlerEx.get_cleaned_link(url)
        self.browser = browser

    def get_props(self, input_props=None):
        if not input_props:
            input_props = {}

        url_ex = UrlHandlerEx(self.url)

        all_properties = url_ex.get_properties()

        if all_properties:
            properties = url_ex.get_section("Properties")
            entries = url_ex.get_section("Entries")

            if len(entries) > 0:
                return self.get_props_internal(url_ex)
            else:
                if "feeds" in properties:
                    for feed in properties["feeds"]:
                        url_ex_new = UrlHandlerEx(feed)
                        all_properties = url_ex_new.get_properties()
                        if all_properties:
                            entries = url_ex_new.get_section("Entries")
                            if len(entries) > 0:
                                return self.get_props_internal(url_ex_new)

            return self.get_props_internal(url_ex)

    def get_props_internal(self, url_ex, input_props=None):
        if not input_props:
            input_props = {}

        all_properties = url_ex.get_properties()

        if all_properties:
            properties = url_ex.get_section("Properties")
            response = url_ex.get_section("Response")
            entries = url_ex.get_section("Entries")

            if properties:
                props = {}
                props["url"] = url_ex.url
                props["title"] = properties["title"]
                props["description"] = properties["description"]
                props["language"] = properties["language"]
                props["favicon"] = properties["thumbnail"]
                props["status_code"] = response["status_code"]

                if len(entries) > 0:
                    props["source_type"] = SourceDataModel.SOURCE_TYPE_RSS
                else:
                    props["source_type"] = SourceDataModel.SOURCE_TYPE_RSS
                    if "Content-Type":
                        content_type = response["Content-Type"]
                        if content_type:
                            if content_type.find("html") >= 1:
                                props["source_type"] = SourceDataModel.SOURCE_TYPE_PARSE
                            if content_type.find("json") >= 1:
                                props["source_type"] = SourceDataModel.SOURCE_TYPE_JSON
                        else:
                            # This is default mode. It will use default crawling method
                            props["source_type"] = SourceDataModel.SOURCE_TYPE_RSS
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
