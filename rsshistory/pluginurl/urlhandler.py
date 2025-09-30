import traceback
import requests

from ..webtools import (
    Url,
    UrlLocation,
    RemoteServer,
    PageOptions,
    HTTP_STATUS_UNKNOWN,
    HTTP_STATUS_CODE_CONNECTION_ERROR,
    HTTP_STATUS_USER_AGENT,
    HTTP_STATUS_TOO_MANY_REQUESTS,
    HTTP_STATUS_CODE_PAGE_UNSUPPORTED,
    HTTP_STATUS_CODE_EXCEPTION,
    HTTP_STATUS_CODE_SERVER_ERROR,
    HTTP_STATUS_CODE_SERVER_TOO_MANY_REQUESTS,
)
from ..apps import LinkDatabase
from ..models import AppLogging, EntryRules, BlockEntry, Browser
from ..configuration import Configuration


class UrlHandler(Url):
    """
    Provides handler, controller for a link. Should inherit title & description API, just like
    webtools Url.

    You can extend it, provide more handlers.

    The controller job is to provide usefull information about link.
    """

    def __init__(self, url=None, settings=None, url_builder=None):
        if not url_builder:
            url_builder = UrlHandler

        super().__init__(url, settings=settings, url_builder=url_builder)

        if not url or url == "":
            lines = traceback.format_stack()
            line_text = ""
            for line in lines:
                line_text += line

            AppLogging.error(
                "Invalid use of UrlHandler API {};Lines:{}".format(url, line_text)
            )

            return

    def get_init_page_options(self, init_options=None):
        o = super().get_init_page_options(init_options)

        browser_mapping = Browser.get_browser_setup()
        if browser_mapping != []:
            o.mode_mapping = browser_mapping

        rules = EntryRules.get_url_rules(self.url)
        if len(rules) > 0:
            for rule in rules:
                if rule.browser:
                    o.bring_to_front(rule.browser.get_setup())

        return o

    def is_valid(self):
        if not super().is_valid():
            return False

        if self.is_blocked():
            return False

        return True

    def is_blocked(self):
        if EntryRules.is_url_blocked(self.url):
            return True

        properties = self.get_properties()
        if not properties:
            return True

        properties["contents"] = self.get_contents()
        if EntryRules.is_dict_blocked(properties):
            return True

        if not self.is_url_valid():
            return True

        if not self.is_allowed():
            return False

    def is_url_valid(self):
        if not super().is_url_valid():
            return False

        return True

    def __str__(self):
        return "{}".format(self.options)


class UrlHandlerEx(object):
    """ """

    def __init__(self, url=None, settings=None, browsers=None):
        self.url = url

        self.settings = settings
        if not self.settings:
            self.settings = {}

        self.browsers = browsers
        if not browsers:
            self.browsers = Browser.get_browser_setup(string=True)
            self.browsers = self.get_browsers()

        self.all_properties = None

    def get_properties(self):
        if self.all_properties:
            return self.all_properties

        return self.get_properties_internal()

    def get_properties_internal(self):
        config_entry = Configuration.get_object().config_entry
        if config_entry.remote_webtools_server_location:
            if self.is_remote_server_down():
                AppLogging.error(
                    "Cannot ping remote server: {}".format(
                        config_entry.remote_webtools_server_location
                    )
                )
                return

            mode_mapping = self.browsers
            request_server = RemoteServer(config_entry.remote_webtools_server_location)

            return self.get_properties_internal_mode_mapping(
                request_server, mode_mapping
            )

    def get_properties_internal_mode_mapping(self, request_server, mode_mapping):
        config_entry = Configuration.get_object().config_entry
        name = ""

        # try default server setup
        self.all_properties = request_server.get_getj(self.url)
        if self.all_properties:
            if not self.is_another_request_necessary():
                return self.all_properties

        if mode_mapping and len(mode_mapping) > 0:
            for crawler_data in mode_mapping:
                if "name" in crawler_data:
                    name = crawler_data["name"]

                AppLogging.debug(
                    "Url:{} Remote server request.\nCrawler:{}\nSettings:{}".format(
                        self.url, name, crawler_data["settings"]
                    )
                )

                self.all_properties = request_server.get_getj(
                    self.url,
                    name=crawler_data["name"],
                    settings=crawler_data,
                )
                if not self.all_properties:
                    AppLogging.warning(
                        "Url:{} Could not communicate with remote server, crawler_data:{}".format(
                            self.url, str(crawler_data)
                        )
                    )
                    continue

                if self.is_server_error():
                    raise IOError(f"{self.url}: Crawling server error")

                """
                # TODO if not valid -> we can retry using a different crawler
                if response is valid (or 403, or redirect?).
                but we have not normal properties, like title, retry using next crawler?
                """

                if self.is_another_request_necessary():
                    continue

                if self.all_properties:
                    return self.all_properties
        else:
            self.all_properties = request_server.get_getj(self.url)
            if not self.all_properties:
                AppLogging.warning(
                    "Url:{} Could not communicate with remote server".format(self.url)
                )

        if not self.all_properties:
            self.all_properties = []

        return self.all_properties

    def get_browsers(self):
        browsers = self.browsers

        rules = EntryRules.get_url_rules(self.url)
        if len(rules) > 0:
            for rule in rules:
                if rule.browser:
                    browsers = self.bring_to_front(
                        browsers, rule.browser.get_setup(True)
                    )

        return browsers

    def bring_to_front(self, browsers, input_data):
        result = [input_data]
        for mode_data in browsers:
            if mode_data == input_data:
                continue

            result.append(mode_data)

        return result

    def get_title(self):
        properties = self.get_section("Properties")
        if not properties:
            return

        if "title" in properties:
            return properties["title"]

    def get_description(self):
        properties = self.get_section("Properties")
        if not properties:
            return

        if "description" in properties:
            return properties["description"]

    def get_language(self):
        properties = self.get_section("Properties")
        if not properties:
            return

        if "language" in properties:
            return properties["language"]

    def get_author(self):
        properties = self.get_section("Properties")
        if not properties:
            return

        if "author" in properties:
            return properties["author"]

    def get_album(self):
        properties = self.get_section("Properties")
        if not properties:
            return

        if "album" in properties:
            return properties["album"]

    def get_thumbnail(self):
        properties = self.get_section("Properties")
        if not properties:
            return

        if "thumbnail" in properties:
            return properties["thumbnail"]

    def is_status_code_invalid(self, status_code):
        """
        Only page statuses
        """
        if status_code >= 200 and status_code <= 400:
            return False

        if status_code == HTTP_STATUS_UNKNOWN:
            return False
        if status_code == HTTP_STATUS_USER_AGENT:
            return False
        if status_code == HTTP_STATUS_TOO_MANY_REQUESTS:
            return False
        if status_code == HTTP_STATUS_CODE_SERVER_TOO_MANY_REQUESTS:
            return False

        return True

    def is_another_request_necessary(self):
        """
        Commonly, if user agent is not welcome
        """
        response = self.get_section("Response")
        if not response:
            return False

        if "status_code" in response:
            status_code = response["status_code"]
            if status_code == HTTP_STATUS_USER_AGENT:
                return True

            if status_code == HTTP_STATUS_TOO_MANY_REQUESTS:
                return True

            if status_code == HTTP_STATUS_CODE_CONNECTION_ERROR:
                return False

            if status_code == HTTP_STATUS_CODE_PAGE_UNSUPPORTED:
                return False

            if status_code == HTTP_STATUS_CODE_SERVER_ERROR:
                #server error might be on one crawler, but does not have to be in another
                return True

            if status_code == HTTP_STATUS_CODE_SERVER_TOO_MANY_REQUESTS:
                return True

            return self.is_status_code_invalid(status_code)

    def get_contents(self):
        """
        @depricated
        """
        return self.get_text()

    def get_text(self):
        contents_data = self.get_section("Text")
        if not contents_data:
            return

        if "Contents" in contents_data:
            return contents_data["Contents"]

    def get_binary(self):
        contents_data = self.get_section("Binary")
        if not contents_data:
            return

        if "Contents" in contents_data:
            return contents_data["Contents"]

    def get_section(self, section_name):
        properties = self.get_properties()
        if not properties:
            return

        if len(properties) == 0:
            return

        request_server = RemoteServer("test")
        return request_server.read_properties_section(section_name, properties)

    def is_valid(self):
        response = self.get_section("Response")
        if not response:
            return False

        if not response["is_valid"]:
            return False

        blocked = self.is_blocked()
        if blocked:
            AppLogging.error("Url:{} not valid:{}".format(self.url, blocked))
            return False

        return True

    def is_invalid(self):
        response = self.get_section("Response")
        if not response:
            return False

        if response["is_invalid"]:
            return True

        blocked = self.is_blocked()
        if blocked:
            AppLogging.error("Url:{} not valid:{}".format(self.url, blocked))
            return True

        return False

    def is_server_error(self):
        if not self.all_properties:
            return False

        response = self.get_section("Response")
        if not response:
            return False

        status_code = response.get("status_code")

        if status_code == HTTP_STATUS_CODE_SERVER_ERROR:
            return True
        if status_code == HTTP_STATUS_CODE_SERVER_TOO_MANY_REQUESTS:
            return True

    def is_blocked(self):
        reason = EntryRules.is_url_blocked(self.url)
        if reason:
            return True

        config_entry = Configuration.get_object().config_entry
        if config_entry.remote_webtools_server_location:
            properties = self.get_section("Properties")
            if not properties:
                return True

            properties["contents"] = self.get_contents()

            reason = EntryRules.is_dict_blocked(properties)
            if reason:
                return reason

        if not self.is_url_valid():
            return True

        if not self.is_allowed():
            return True

        return False

    def get_block_reason(self):
        if EntryRules.is_url_blocked(self.url):
            return "EntryUrl Url block"

        properties = self.get_section("Properties")
        if not properties:
            return "Missing properties"

        properties["contents"] = self.get_contents()

        status = EntryRules.is_dict_blocked(properties)
        if status:
            return "Dict block: {}".format(status)

        if not self.is_url_valid():
            return "Url not valid"

        if not self.is_allowed():
            return "Not Allowed"

    def __str__(self):
        return "{}".format(self.options)

    def ping(url, timeout_s=20):
        config_entry = Configuration.get_object().config_entry
        remote_server = RemoteServer(config_entry.remote_webtools_server_location)
        status = remote_server.get_pingj(url)

        return status

    def get_cleaned_link(url):
        return Url.get_cleaned_link(url)

    def is_remote_server_down(self):
        config_entry = Configuration.get_object().config_entry
        if config_entry.remote_webtools_server_location:
            if not UrlHandlerEx.ping(config_entry.remote_webtools_server_location):
                return True

    def is_url_valid(self):
        return True

    def is_allowed(self):
        response = self.get_section("Response")
        if not response:
            return False

        return response.get("is_allowed")

    def get_response(self):
        self.get_properties()
        config_entry = Configuration.get_object().config_entry
        server = RemoteServer(config_entry.remote_webtools_server_location)
        return server.get_response(self.all_properties)
