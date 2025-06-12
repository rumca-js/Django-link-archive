from utils.dateutils import DateUtils
from utils.inputcontent import InputContent
from ..webtools import (
    HtmlPage,
    RssPage,
    UrlLocation,
    DefaultContentPage,
    HttpPageHandler,
    RemoteServer,
)

from ..apps import LinkDatabase
from ..controllers import SourceDataController
from ..configuration import Configuration
from ..models import AppLogging, EntryRules

from .urlhandler import UrlHandlerEx


class YouTubeException(Exception):
    pass


class EntryUrlInterface(object):
    """
    Provides interface between Entry and URL properties.
    """

    def __init__(self, url, log=False, ignore_errors=False, browser=None):
        """
        Some scenarios, like manual entry should log why it is impossible to check
        TODO maybe add ignore_errors, so we could add any kind of link?
        """
        self.log = log
        self.ignore_errors = ignore_errors
        self.props = None
        self.all_properties = None
        self.browser = None

        self.url = UrlHandlerEx.get_cleaned_link(url)
        self.handler = None

    def get_response(self):
        return self.response

    def get_props(self, input_props=None, source_obj=None):
        if not input_props:
            input_props = {}

        props = None

        browsers = None
        if self.browser:
            browsers = [browser.get_setup()]

        url_ex = UrlHandlerEx(self.url, browsers=browsers)
        self.handler = url_ex

        self.all_properties = url_ex.get_properties()

        if self.all_properties:
            properties = url_ex.get_section("Properties")
            response = url_ex.get_section("Response")

            # TODO properties["date_dead_since"] = DateUtils.get_datetime_now_utc()

            props = properties

            if props:
                if response and "status_code" in response:
                    props["status_code"] = response["status_code"]
                else:
                    props["status_code"] = 0

        # we do not trim description here. We might need it later, when adding link we scan
        # description for URLs

        if props:
            self.fix_properties(props, source_obj=source_obj)
        elif self.ignore_errors:
            props = {}
            props["link"] = self.url
            props["title"] = None
            props["description"] = None
            props["author"] = None
            props["language"] = None
            props["age"] = None
            props["thumbnail"] = None
            props["date_published"] = None
            props["date_dead_since"] = DateUtils.get_datetime_now_utc()
            props["page_rating"] = 0
            props["dead"] = True
            props["status_code"] = 0

            self.fix_properties(props, source_obj=source_obj)

        self.props = props

        return props

    def get_props_implementation(self, input_props=None, source_obj=None):
        if not input_props:
            input_props = {}

        return input_props

    def is_valid(self):
        if not self.all_properties:
            return False

        if not self.handler:
            return False

        if not self.handler.is_valid():
            return False

        server = RemoteServer("https://")
        response = server.read_properties_section("Response", self.all_properties)
        if "is_valid" in response:
            return response["is_valid"]

        return True

    def fix_properties(self, input_props=None, source_obj=None):
        if not input_props:
            input_props = {}
            # some Internet sources provide invalid publication date

        if input_props:
            if isinstance(input_props.get("date_published"), str):
                input_props["date_published"] = DateUtils.parse_datetime(
                    input_props["date_published"]
                )

        if not self.is_property_set(input_props, "description"):
            cm = InputContent(input_props["description"])
            input_props["description"] = cm.strip_html_attrs()

        age = EntryRules.get_age_for_dictionary(input_props)
        if age:
            input_props["age"] = age

        if self.is_property_set(input_props, "date_published"):
            if input_props["date_published"] > DateUtils.get_datetime_now_utc():
                input_props["date_published"] = DateUtils.get_datetime_now_utc()

        if self.is_property_set(
            input_props, "date_last_modified"
        ) and self.is_property_set(input_props, "date_published"):
            if input_props["date_last_modified"] < input_props["date_published"]:
                input_props["date_published"] = input_props["date_last_modified"]

        is_domain = UrlLocation(self.url).is_domain()

        c = Configuration.get_object().config_entry

        if not source_obj:
            sources = SourceDataController.objects.filter(url=self.url)
            if sources.exists():
                source_obj = sources[0]

        if not self.is_property_set(input_props, "source_url") and source_obj:
            input_props["source_url"] = source_obj.url

        if not self.is_property_set(input_props, "source") and source_obj:
            input_props["source"] = source_obj

        if (
            not self.is_property_set(input_props, "language")
            and source_obj
            and source_obj.language
        ):
            input_props["language"] = source_obj.language

        """
        Sometimes we want thumbnail sometimes we want favicon.
         - for search engine we want to store path to favicon if thumbnail is not available
         - for domains we want to store path to favicon if thumbnail is not available
         - for not domains? this is not clear cut. If entry is obtained by source, then source thumbnail should be displayed
        """

        is_domain = UrlLocation(self.url).is_domain()
        request_server = RemoteServer(c.remote_webtools_server_location)
        properties = request_server.read_properties_section(
            "Properties", self.all_properties
        )
        if is_domain and properties and "favicon" in properties:
            input_props["thumbnail"] = properties["favicon"]

        if not self.is_property_set(input_props, "page_rating_contents"):
            if self.is_property_set(input_props, "page_rating"):
                input_props["page_rating_contents"] = input_props["page_rating"]
            else:
                input_props["page_rating_contents"] = 0

        if not self.is_property_set(input_props, "date_dead_since"):
            input_props["date_dead_since"] = None

        return input_props

    def is_property_set(self, input_props, property):
        return property in input_props and input_props[property]
