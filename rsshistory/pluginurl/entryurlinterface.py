from utils.dateutils import DateUtils
from ..webtools import (
    HtmlPage,
    RssPage,
    DomainAwarePage,
    DefaultContentPage,
    HttpPageHandler,
    UrlAgeModerator,
)

from ..apps import LinkDatabase
from ..controllers import SourceDataController
from ..configuration import Configuration
from ..models import AppLogging

from .urlhandler import UrlHandler


class YouTubeException(Exception):
    pass


class EntryUrlInterface(object):
    """
    Provides interface between Entry and URL properties.
    """

    def __init__(
        self,
        url,
        log=False,
        ignore_errors=False,
    ):
        """
        Some scenarios, like manual entry should log why it is impossible to check
        TODO maybe add ignore_errors, so we could add any kind of link?
        """
        self.log = log
        self.ignore_errors = ignore_errors
        self.props = None

        self.url = UrlHandler.get_cleaned_link(url)

        h = UrlHandler(url)
        self.options = h.options

    def make_request(self):
        self.u = UrlHandler(self.url, page_options=self.options)
        self.response = self.u.get_response()

        if self.response:
            self.url = self.response.url

        if not self.ignore_errors and not self.u.is_valid():
            if self.log:
                AppLogging.error("Page is invalid:{}".format(url))

    def get_response(self):
        return self.response

    def get_props(self, input_props=None, source_obj=None):
        self.make_request()

        if not input_props:
            input_props = {}

        if not self.ignore_errors and not self.u.is_valid():
            return

        ignore_errors = self.ignore_errors

        # we do not trim description here. We might need it later, when adding link we scan
        # description for URLs

        props = self.get_props_implementation(input_props, source_obj=source_obj)
        if props:
            self.fix_properties(props)
        elif ignore_errors:
            """
            TODO should be set any part from self.u?
            """
            props = {}
            props["link"] = self.url
            props["title"] = None
            props["description"] = None
            props["author"] = None
            props["language"] = None
            props["thumbnail"] = None
            props["date_published"] = DateUtils.get_datetime_now_utc()
            props["date_dead_since"] = DateUtils.get_datetime_now_utc()
            props["page_rating"] = 0
            props["dead"] = True
            props["page_rating_contents"] = 0
            props["status_code"] = self.u.get_status_code()

        self.props = props

        return props

    def get_props_implementation(self, input_props=None, source_obj=None):
        if not input_props:
            input_props = {}

        if not self.u:
            return None

        if not self.is_property_set(input_props, "source_url"):
            if source_obj:
                input_props["source_url"] = source_obj.url

        is_domain = DomainAwarePage(self.url).is_domain()
        handler = self.u.get_handler()

        c = Configuration.get_object().config_entry

        if is_domain:
            if c.keep_domains:
                input_props["permanent"] = True
            input_props["bookmarked"] = False

        if not source_obj:
            sources = SourceDataController.objects.filter(url=self.url)
            if sources.exists():
                source_obj = sources[0]

        if not self.is_property_set(input_props, "source") and source_obj:
            input_props["source"] = source_obj

        if not self.is_property_set(input_props, "source_url") and source_obj:
            input_props["source_url"] = source_obj.url

        input_props = self.update_info_default(input_props, source_obj)
        return input_props

    def is_update_supported(self):
        """
        TODO how to make this check automatically?
        """
        if not self.u:
            return None

        p = self.u.get_handler()

        if type(p) is not DefaultContentPage:
            return True

        return False

    def is_valid(self):
        if not self.u.is_valid():
            return False

        # we support the type, but we do not provide valid properties
        props = self.props
        if not props and self.is_update_supported():
            return False

        return True

    def update_info_default(self, input_props=None, source_obj=None):
        if not input_props:
            input_props = {}

        url = self.url
        p = self.u.get_handler()

        if not self.is_property_set(input_props, "link"):
            input_props["link"] = self.u.get_clean_url()
        if not self.is_property_set(input_props, "title"):
            input_props["title"] = self.u.get_title()
        if not self.is_property_set(input_props, "description"):
            input_props["description"] = self.u.get_description()
        if not self.is_property_set(input_props, "language"):
            input_props["language"] = self.u.get_language()
        if not self.is_property_set(input_props, "thumbnail"):
            input_props["thumbnail"] = self.u.get_thumbnail()
        if not self.is_property_set(input_props, "author"):
            input_props["author"] = self.u.get_author()
        if not self.is_property_set(input_props, "album"):
            input_props["album"] = self.u.get_album()
        if not self.is_property_set(input_props, "page_rating_contents"):
            input_props["page_rating_contents"] = self.u.get_page_rating()
        if not self.is_property_set(input_props, "page_rating"):
            input_props["page_rating"] = 0  # unset
        if not self.is_property_set(input_props, "status_code"):
            input_props["status_code"] = self.u.get_status_code()
        if not self.is_property_set(input_props, "contents_hash"):
            input_props["contents_hash"] = self.u.get_contents_hash()
        if not self.is_property_set(input_props, "contents_body_hash"):
            input_props["contents_body_hash"] = self.u.get_contents_body_hash()
        if not self.is_property_set(input_props, "date_last_modified"):
            if self.response:
                input_props["date_last_modified"] = self.response.get_last_modified()

        if not self.is_property_set(input_props, "language") and source_obj and source_obj.language:
            input_props["language"] = source_obj.language

        if not self.is_property_set(input_props, "age"):
            if self.is_property_set(input_props, "title") and self.is_property_set(
                input_props, "description"
            ):
                properties = {
                    "title": input_props["title"],
                    "description": input_props["description"],
                }
                moderator = UrlAgeModerator(properties=properties)
                input_props["age"] = moderator.get_age()

        """
        Sometimes we want thumbnail sometimes we want favicon.
         - for search engine we want to store path to favicon if thumbnail is not available
         - for domains we want to store path to favicon if thumbnail is not available
         - for not domains? this is not clear cut. If entry is obtained by source, then source thumbnail should be displayed
        """

        is_domain = DomainAwarePage(self.url).is_domain()
        if is_domain and not self.is_property_set(input_props, "thumbnail"):
            if type(p) is HtmlPage and self.u:
                input_props["thumbnail"] = self.u.get_favicon()

        return input_props

    def fix_properties(self, input_props=None):
        if not input_props:
            input_props = {}
            # some Internet sources provide invalid publication date

        if self.is_property_set(input_props, "date_published"):
            if input_props["date_published"] > DateUtils.get_datetime_now_utc():
                input_props["date_published"] = DateUtils.get_datetime_now_utc()

        if self.is_property_set(
            input_props, "date_last_modified"
        ) and self.is_property_set(input_props, "date_published"):
            if input_props["date_last_modified"] < input_props["date_published"]:
                input_props["date_published"] = input_props["date_last_modified"]

        if not self.u.is_valid():
            input_props["date_dead_since"] = DateUtils.get_datetime_now_utc()
        else:
            input_props["date_dead_since"] = None

        return input_props

    def is_property_set(self, input_props, property):
        return property in input_props and input_props[property]
