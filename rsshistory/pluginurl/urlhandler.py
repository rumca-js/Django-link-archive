import traceback
import requests

from ..webtools import (
    Url,
    UrlLocation,
    RemoteServer,
    PageOptions,
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

        config = Configuration.get_object().config_entry
        o.ssl_verify = config.ssl_verification

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

            config_entry = Configuration.get_object().config_entry
            if config_entry.respect_robots_txt:
                self.settings["respect_robots_txt"] = True
            if config_entry.ssl_verification:
                self.settings["ssl_verify"] = True

        self.browsers = browsers
        if not browsers:
            self.browsers = Browser.get_browser_setup()
            self.browsers = self.get_browsers()

        self.all_properties = None

    def get_properties(self):
        if self.all_properties:
            return self.all_properties

        return self.get_properties_internal()

    def get_properties_internal(self):
        config_entry = Configuration.get_object().config_entry
        if config_entry.remote_webtools_server_location:
            request_server = RemoteServer(config_entry.remote_webtools_server_location)

            if self.is_remote_server_down():
                AppLogging.error(
                    "Cannot ping remote server: {}".format(
                        config_entry.remote_webtools_server_location
                    )
                )
                return

            mode_mapping = self.browsers

            return self.get_properties_internal_mode_mapping(
                request_server, mode_mapping
            )

    def get_properties_internal_mode_mapping(self, request_server, mode_mapping):
        config_entry = Configuration.get_object().config_entry
        name = ""
        if mode_mapping and len(mode_mapping) > 0:
            for crawler_data in mode_mapping:
                crawler_data = self.get_ready_crawler_data(crawler_data)
                if "name" in crawler_data:
                    name = crawler_data["name"]

                AppLogging.debug(
                    "Url:{} Calling with name {} and settings {}".format(
                        self.url, name, crawler_data["settings"]
                    )
                )

                self.all_properties = request_server.get_getj(
                    self.url,
                    name=crawler_data["name"],
                    settings=crawler_data["settings"],
                )
                if not self.all_properties:
                    AppLogging.warning(
                        "Url:{} Could not communicate with remote server, crawler_data:{}".format(
                            self.url, str(crawler_data)
                        )
                    )
                    continue

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

    def get_ready_crawler_data(self, crawler_data):
        config_entry = Configuration.get_object().config_entry

        crawler_data = self.get_ready_browser(crawler_data)
        if not crawler_data:
            return

        if config_entry.respect_robots_txt:
            crawler_data["settings"]["respect_robots_txt"] = True
        else:
            crawler_data["settings"]["respect_robots_txt"] = False
        if config_entry.ssl_verification:
            crawler_data["settings"]["ssl_verify"] = True
        else:
            crawler_data["settings"]["ssl_verify"] = False
        # TODO add proxy support
        # TODO add user agent
        # TODO add headers?

        return crawler_data

    def get_ready_browser(self, crawler_data):
        config_entry = Configuration.get_object().config_entry

        for settings_key in self.settings:
            crawler_data["settings"][settings_key] = self.settings[settings_key]

        if "ssl_verify" not in crawler_data["settings"]:
            crawler_data["settings"]["ssl_verify"] = config_entry.ssl_verification

        return crawler_data

    def get_browsers(self):
        browsers = self.browsers

        rules = EntryRules.get_url_rules(self.url)
        if len(rules) > 0:
            for rule in rules:
                if rule.browser:
                    browsers = self.bring_to_front(browsers, rule.browser.get_setup())

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

    def is_another_request_necessary(self):
        """
        Commonly, if user agent is not welcome, 403 is displayed
        """
        response = self.get_section("Response")
        if not response:
            return False

        if "status_code" in response:
            if response["status_code"] == 403:
                return True

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

        if self.is_blocked():
            return False

        return True

    def is_blocked(self):
        properties = self.get_section("Properties")

        if EntryRules.is_url_blocked(self.url):
            return True

        properties = self.get_section("Properties")
        if EntryRules.is_dict_blocked(properties):
            return True

        if not self.is_url_valid():
            return True

        if not self.is_allowed():
            return True

        return False

    def __str__(self):
        return "{}".format(self.options)

    def ping(url, timeout_s = 20, user_agent=None):
        if not user_agent:
            config_entry = Configuration.get_object().config_entry
            if config_entry.user_agent:
                user_agent = config_entry.user_agent

        u = Url(url)
        return u.ping(timeout_s = timeout_s, user_agent=user_agent)

    def get_cleaned_link(url):
        return Url.get_cleaned_link(url)

    def is_remote_server_down(self):
        config_entry = Configuration.get_object().config_entry
        if config_entry.remote_webtools_server_location:
            request_server = RemoteServer(config_entry.remote_webtools_server_location)

            if not UrlHandlerEx.ping(config_entry.remote_webtools_server_location):
                return True

    def is_url_valid(self):
        return True

    def is_allowed(self):
        config_entry = Configuration.get_object().config_entry
        if config_entry.respect_robots_txt:
            response = self.get_section("Response")
            if response:
                if "is_allowed" in response and not response["is_allowed"]:
                    return False

            return True
        else:
            return True

    def get_response(self):
        self.get_properties()
        config_entry = Configuration.get_object().config_entry
        server = RemoteServer(config_entry.remote_webtools_server_location)
        return server.get_response(self.all_properties)
