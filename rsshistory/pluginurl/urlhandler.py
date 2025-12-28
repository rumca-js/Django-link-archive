import traceback
import requests
import json

from webtoolkit import (
    RemoteServer,
    RemoteUrl,
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


class UrlHandler(object):
    """ """

    def __init__(self, url=None, browsers=None, last_browser=None, entry=None, handler_name=None):
        if entry and not url:
            url = entry.link

        self.url = url
        self.entry = entry

        self.handler_name = handler_name
        if entry:
            self.last_browser = entry.last_browser
        else:
            self.last_browser = last_browser

        self.browsers = browsers
        if not browsers:
            self.browsers = Browser.get_browsers()
            self.browsers = self.get_browsers()

        self.all_properties = None

    def get_properties(self):
        if self.all_properties:
            return self.all_properties

        return self.get_properties_internal()

    def get_properties(self):
        properties = self.get_section("Properties")
        if not properties:
            return

        return properties

    def get_all_properties(self):
        if self.all_properties:
            return self.all_properties

        self.all_properties = self.get_properties_internal()
        return self.all_properties

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
                self.last_browser = browser

                AppLogging.debug(
                    "Url:{} Remote server request.\nBrowser:{}".format(
                        self.url, browser,
                    )
                )

                request = self.browser_to_request(browser)

                self.all_properties = request_server.get_getj(request=request)
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
                    if self.entry:
                        self.entry.last_browser = self.last_browser
                        self.entry.save()

                    return self.all_properties
        else:
            request = PageRequestObject(self.url)

            self.all_properties = request_server.get_getj(request=request)
            if not self.all_properties:
                AppLogging.warning(
                    "Url:{} Could not communicate with remote server".format(self.url)
                )

            if self.all_properties:
                if self.entry:
                    self.entry.last_browser = self.last_browser
                    self.entry.save()
                return self.all_properties

        if not self.all_properties:
            self.all_properties = []

        return self.all_properties

    def is_another_request_necessary(self):
        """
        Commonly, if user agent is not welcome
        """
        response = self.get_response()
        if not response:
            return False

        status_code = response.status_code

        if status_code == HTTP_STATUS_CODE_CONNECTION_ERROR:
            return False

        if status_code == HTTP_STATUS_CODE_PAGE_UNSUPPORTED:
            return False

        # even though we receive 404 the site might detect our bot
        # so we can attempt with other crawlers

        return not is_status_code_valid(status_code)

    def browser_to_request(self, browser):
        request = PageRequestObject(self.url)

        request.user_agent = browser.user_agent
        if browser.request_headers:
            try:
                request.request_headers = json.loads(browser.request_headers)
            except Exception as E:
                print(E)
        request.timeout_s = browser.timeout_s
        request.delay_s = browser.delay_s
        request.ssl_verify = browser.ssl_verify
        request.respect_robots = browser.respect_robots_txt
        request.accept_types = browser.accept_types
        request.bytes_limit = browser.bytes_limit
        request.http_proxy = browser.http_proxy
        request.https_proxy = browser.https_proxy

        if browser.cookies:
            try:
                request.cookies = json.loads(browser.cookies)
            except Exception as E:
                print(E)
        if browser.settings:
            try:
                request.settings = json.loads(browser.settings)
            except Exception as E:
                print(E)

        request.crawler_name = browser.name
        if self.handler_name:
            request.handler_name = self.handler_name
        elif browser.handler_name:
            request.handler_name = browser.handler_name

        return request

    def get_browsers(self):
        browsers = self.browsers

        if self.last_browser:
            browsers = self.bring_to_front(
                 browsers, self.last_browser.id
            )

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

        id_browsers = Browser.objects.filter(id = browser_id)
        if id_browsers.exists():
            result.append(id_browsers[0])

        for browser in browsers:
            if browser.id == browser_id:
                continue

            result.append(browser)

        return result

    def get_title(self):
        return self.get_properties().get("title")

    def get_description(self):
        return self.get_properties().get("description")

    def get_language(self):
        return self.get_properties().get("language")

    def get_author(self):
        return self.get_properties().get("author")

    def get_album(self):
        return self.get_properties().get("album")

    def get_thumbnail(self):
        return self.get_properties().get("thumbnail")

    def get_text(self):
        response = self.get_response()
        if response:
            return response.get_text()

    def get_binary(self):
        response = self.get_response()
        if response:
            return response.get_binary()

    def get_section(self, section_name):
        properties = self.get_all_properties()
        if not properties:
            return

        if len(properties) == 0:
            return

        return RemoteServer.read_properties_section(section_name, properties)

    def is_valid(self):
        response = self.get_response()
        if not response:
            return False

        if not response.is_valid():
            return False

        blocked = self.is_blocked()
        if blocked:
            AppLogging.error("Url:{} not valid:{}".format(self.url, blocked))
            return False

        return True

    def is_invalid(self):
        response = self.get_response()
        if not response:
            return False

        if response.is_invalid():
            return True

        blocked = self.is_blocked()
        if blocked:
            AppLogging.error("Url:{} not valid:{}".format(self.url, blocked))
            return True

        return False

    def is_server_error(self):
        if not self.all_properties:
            return False

        response = self.get_response()
        if not response:
            return False

        status_code = response.status_code

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

            properties["contents"] = self.get_text()

            reason = EntryRules.is_dict_blocked(properties)
            if reason:
                return reason

        if not self.is_allowed():
            return True

        return False

    def get_block_reason(self):
        if EntryRules.is_url_blocked(self.url):
            return "EntryUrl Url block"

        properties = self.get_section("Properties")
        if not properties:
            return "Missing properties"

        response = self.get_response()
        if not response:
            return "No response"

        properties["contents"] = response.get_text()

        status = EntryRules.is_dict_blocked(properties)
        if status:
            return "Dict block: {}".format(status)

        if self.is_invalid():
            return "Url is not valid"

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
            if not UrlHandler.ping(config_entry.remote_webtools_server_location):
                return True

    def is_allowed(self):
        response = self.get_response()
        if not response:
            return False

        return response.is_allowed()

    def get_response(self):
        self.get_properties()
        config_entry = Configuration.get_object().config_entry
        return RemoteUrl(all_properties = self.all_properties).get_response()
