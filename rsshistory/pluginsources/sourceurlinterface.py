import json
from webtoolkit import (
    HtmlPage,
    RssPage,
    JsonPage,
    UrlLocation,
)
from utils.services import OpenRss

from ..models import (
    SourceDataModel,
)
from ..configuration import Configuration
from ..pluginsources.sourceparseplugin import BaseParsePlugin
from ..pluginurl.urlhandler import UrlHandler


class SourceUrlInterface(object):
    """
    Provides interface between Source and URL Properties
    Used by forms creator
    """

    def __init__(self, url, browser=None):
        self.url = UrlHandler.get_cleaned_link(url)
        self.browser = browser
        self.url_ex = None
        self.all_properties = None

    def get_props(self, input_props=None):
        self.url_ex = self.get_url(input_props)
        self.all_properties = self.url_ex.get_properties()
        response = self.url_ex.get_response()
        is_json = response.is_content_json()
        if is_json:
            return self.get_props_from_json(self.url_ex)
        else:
            return self.get_props_from_url(self.url_ex)

    def get_url(self, input_props=None):
        if not input_props:
            input_props = {}

        url_ex = UrlHandler(self.url)

        all_properties = url_ex.get_properties()

        if all_properties:
            properties = url_ex.get_properties()
            entries = url_ex.get_entries()

            if len(entries) > 0:
                return url_ex
            else:
                if "feeds" in properties:
                    for feed in properties["feeds"]:
                        url_ex_new = UrlHandler(feed)
                        all_properties = url_ex_new.get_properties()
                        if all_properties:
                            entries = url_ex_new.get_section("Entries")
                            if len(entries) > 0:
                                return url_ex_new

            return url_ex

    def get_props_from_url(self, url_ex, input_props=None):
        if not input_props:
            input_props = {}

        all_properties = url_ex.get_properties()

        if all_properties:
            properties = url_ex.get_properties()
            response = url_ex.get_response()
            entries = url_ex.get_entries()

            if properties:
                props = {}
                props["url"] = url_ex.url
                props["title"] = properties["title"]
                props["description"] = properties["description"]
                props["language"] = properties["language"]
                props["favicon"] = properties["thumbnail"]
                props["status_code"] = response.status_code

                if response.is_content_rss():
                    props["source_type"] = SourceDataModel.SOURCE_TYPE_RSS
                elif len(entries) > 0:
                    props["source_type"] = SourceDataModel.SOURCE_TYPE_DEFAULT
                else:
                    if "Content-Type":
                        is_json = response.is_content_json()
                        if is_json:
                            props["source_type"] = SourceDataModel.SOURCE_TYPE_JSON
                if "source_type" not in props or props["source_type"] is None:
                    props["source_type"] = SourceDataModel.SOURCE_TYPE_PARSE
        else:
            props = {}

        if "status_code" not in props:
            if self.u:
                props["status_code"] = self.u.get_status_code()

        self.fix_props(url_ex, props)

        return props

    def get_props_from_json(self, url_ex, input_props=None):
        if not input_props:
            input_props = {}

        response = url_ex.get_response()
        text = response.get_text()
        json_object = json.loads(text)

        if "source" in json_object:
            props = json_object["source"]
        else:
            return self.get_props_from_url(self.url_ex)

        self.fix_props(url_ex, props)
        return props

    def fix_props(self, url_ex, input_props):
        if "remove_after_days" not in input_props:
            input_props["remove_after_days"] = 0
        if "fetch_period" not in input_props:
            input_props["fetch_period"] = "3600"
        if "age" not in input_props:
            input_props["age"] = 0
        if "status_code" not in input_props:
            input_props["status_code"] = 0
        if "language" not in input_props or input_props["language"] is None:
            input_props["language"] = ""
        if "category_name" not in input_props or input_props["category_name"] is None:
            input_props["category_name"] = "New"
        if "subcategory_name" not in input_props or input_props["subcategory_name"] is None:
            input_props["subcategory_name"] = "New"

        return input_props

    def is_property_set(self, input_props, property):
        return property in input_props and input_props[property]
