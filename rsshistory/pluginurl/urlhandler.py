import traceback
import requests

from webtoolkit import (
    RemoteServer,
    UrlLocation,
    PageRequestObject,
    is_status_code_valid,
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


class UrlHandlerEx(object):
    """ """

    def __init__(self, url=None, settings=None, browsers=None):
        self.url = url

        self.settings = settings
        if not self.settings:
            self.settings = {}

        self.browsers = browsers
        if not browsers:
            self.browsers = Browser.get_browsers()
            self.browsers = self.get_browsers()

        self.all_properties = None

    def get_properties(self):
        if self.all_properties:
            return self.all_properties

        return self.get_properties_internal()

    def get_properties_internal(self):
        config_entry = Configuration.get_object().config_entry

        remote_server = Configuration.get_object().get_remote_server()
        if remote_server:
            if self.is_remote_server_down():
                AppLogging.error(
                    "Cannot ping remote server: {}".format(
                        config_entry.remote_webtools_server_location
                    )
                )
                return

            return self.get_properties_internal_mode_mapping(
                remote_server, self.browsers
            )

    def get_properties_internal_mode_mapping(self, request_server, browsers):
        config_entry = Configuration.get_object().config_entry
        name = ""

        # Here was code to call "default" crawler from crawler buddy
        # This might end up with 2 selenium calls, where here, one later

        if browsers and len(browsers) > 0:
            for browser in browsers:
                AppLogging.debug(
                    "Url:{} Remote server request.\nBrowser:{}".format(
                        self.url, browser,
                    )
                )

                request = self.browser_to_request(browser)

                self.all_properties = request_server.get_getj(request)
                if not self.all_properties:
                    AppLogging.warning(
                        "Url:{} Could not communicate with remote server, Browser:{}".format(
                            self.url, browser
                        )
                    )
                    continue

                if self.is_server_error() and not browser.ignore_errors:
                    AppLogging.debug(f"{self.url}: Crawling server error",
                               detail_text = str(self.all_properties))
                    raise IOError(f"{self.url}: Crawling server error")

                """
                # TODO if not valid -> we can retry using a different crawler
                if response is valid (or 403, or redirect?).
                but we have not normal properties, like title, retry using next crawler?

                Requests are blocked by some sites (politico?)
                Stealth requests does not work for others (reddit gives 503).
                """

                if self.is_another_request_necessary():
                    AppLogging.warning("Url:{} Trying another crawler".format(self.url),
                       detail_text = str(self.all_properties))
                    continue

                if self.all_properties:
                    return self.all_properties
        else:
            request = PageRequestObject(self.url)

            self.all_properties = request_server.get_getj(request)
            if not self.all_properties:
                AppLogging.warning(
                    "Url:{} Could not communicate with remote server".format(self.url)
                )

        if not self.all_properties:
            self.all_properties = []

        return self.all_properties

    def browser_to_request(self, browser):
        request = PageRequestObject(self.url)
        request.crawler_name = browser.name
        return request

    def get_browsers(self):
        browsers = self.browsers

        rules = EntryRules.get_url_rules(self.url)
        if len(rules) > 0:
            for rule in rules:
                if rule.browser:
                    browsers = self.bring_to_front(
                        browsers, rule.browser.id
                    )

        return browsers

    def bring_to_front(self, browsers, browser_id):
        result = []

        id_browsers = Browsers.objects.filter(id = browser_id)
        if id_browsers.exists():
            result.append(id_browsers[0])

        for browser in browsers:
            if browser.id == browser_id:
                continue

            result.append(browser)

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

    def is_another_request_necessary(self):
        """
        Commonly, if user agent is not welcome
        """
        response = self.get_section("Response")
        if not response:
            return False

        if "status_code" in response:
            status_code = response["status_code"]

            if status_code == HTTP_STATUS_CODE_CONNECTION_ERROR:
                return False

            if status_code == HTTP_STATUS_CODE_PAGE_UNSUPPORTED:
                return False

            # even though we receive 404 the site might detect our bot
            # so we can attempt with other crawlers

            return not is_status_code_valid(status_code)

    def get_contents(self):
        """
        @depricated
        """
        return self.get_text()

    def get_text(self):
        contents_data = self.get_section("Streams")
        if not contents_data:
            return

        for item in contents_data:
            if item != "Binary":
                return contents_data[item]

    def get_binary(self):
        contents_data = self.get_section("Streams")
        if not contents_data:
            return

        if "Binary" in contents_data:
            return contents_data["Binary"]

    def get_section(self, section_name):
        properties = self.get_properties()
        if not properties:
            return

        if len(properties) == 0:
            return

        return RemoteServer.read_properties_section(section_name, properties)

    def is_valid(self):
        response = self.get_section("Response")
        if not response:
            return False

        if "is_valid" not in response:
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

        if "is_invalid" in response and response["is_invalid"]:
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

        return False

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
        remote_server = Configuration.get_object().get_remote_server()
        request = PageRequestObject(url)
        status = remote_server.get_pingj(request)

        return status

    def get_cleaned_link(url):
        return UrlLocation.get_cleaned_link(url)

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
        return RemoteServer.get_response(self.all_properties)
