import traceback
import requests

from ..webtools import (
    Url,
    UrlLocation,
    UrlPropertyValidator,
    RemoteServer,
    PageOptions,
)

from ..apps import LinkDatabase
from ..models import AppLogging, EntryRules, BlockEntry
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

        # TODO this is reading overhead. We might cache something?
        from ..models import Browser

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
        keywords = Configuration.get_object().get_blocked_keywords()
        validator = UrlPropertyValidator(
            properties=self.get_properties(), blocked_keywords=keywords
        )
        if len(keywords) > 0:
            validator.blocked_keywords = keywords

        if not validator.is_valid():
            return True

        if EntryRules.is_blocked(self.url):
            return True

        p = UrlLocation(self.url)
        domain_only = p.get_domain_only()

        if BlockEntry.is_blocked(domain_only):
            return True

        if not self.is_url_valid():
            return True

    def is_url_valid(self):
        if not super().is_url_valid():
            return False

        return True

    def __str__(self):
        return "{}".format(self.options)


class UrlHandlerEx(object):
    """
    """

    def __init__(self, url=None, page_options=None, handler_class=None):
        self.url = url

        self.options = page_options
        if not self.options:
            self.options = UrlHandlerEx.get_options(self.url)

        self.handler_class = handler_class
        self.all_properties = None

    def get_properties(self):
        if self.all_properties:
            return self.all_properties

        config_entry = Configuration.get_object().config_entry
        if config_entry.remote_webtools_server_location:
            request_server = RemoteServer(config_entry.remote_webtools_server_location)

            name = ""
            if self.options and self.options.mode_mapping and len(self.options.mode_mapping) > 0:
                for item in self.options.mode_mapping:
                    if self.is_remote_server_down():
                        AppLogging.error("Cannot ping remote server: {}".format(config_entry.remote_webtools_server_location))
                        return

                    self.all_properties = request_server.get_crawlj(self.url, name=item["name"], settings=item["settings"])
                    if not self.all_properties:
                        AppLogging.error("Url:{} Could not communicate with remote server, item:{}".format(self.url, str(item)))
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
                self.all_properties = request_server.get_crawlj(self.url)
                if not self.all_properties:
                    AppLogging.error("Url:{} Could not communicate with remote server".format(self.url))

        if not self.all_properties:
            self.all_properties = []

        return self.all_properties

    def get_title(self):
        properties = self.get_section("Properties")
        if "title" in properties:
            return properties["title"]

    def get_description(self):
        properties = self.get_section("Properties")
        if "description" in properties:
            return properties["description"]

    def get_language(self):
        properties = self.get_section("Properties")
        if "language" in properties:
            return properties["language"]

    def get_author(self):
        properties = self.get_section("Properties")
        if "author" in properties:
            return properties["author"]

    def get_album(self):
        properties = self.get_section("Properties")
        if "album" in properties:
            return properties["album"]

    def get_thumbnail(self):
        properties = self.get_section("Properties")
        if "thumbnail" in properties:
            return properties["thumbnail"]

    def is_another_request_necessary(self):
        """
        Commonly, if user agent is not welcome, 403 is displayed
        """
        response = self.get_section("Response")
        if "status_code" in response:
            if response["status_code"] == 403:
                return True

    def get_contents(self):
        contents = self.get_section("Contents")
        return contents["Contents"]

    def get_section(self, section_name):
        properties = self.get_properties()
        if not properties:
            return

        if len(properties) == 0:
            return

        request_server = RemoteServer("test")
        return request_server.read_properties_section(section_name, properties)

    def get_options(url):
        options = PageOptions()

        from ..models import Browser

        browser_mapping = Browser.get_browser_setup()
        if browser_mapping != []:
            options.mode_mapping = browser_mapping

        rules = EntryRules.get_url_rules(url)
        if len(rules) > 0:
            for rule in rules:
                if rule.browser:
                    options.bring_to_front(rule.browser.get_setup())

        config = Configuration.get_object().config_entry
        options.ssl_verify = config.ssl_verification

        return options

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
        keywords = Configuration.get_object().get_blocked_keywords()
        validator = UrlPropertyValidator(
            properties=self.get_properties(), blocked_keywords=keywords
        )
        if len(keywords) > 0:
            validator.blocked_keywords = keywords

        if not validator.is_valid():
            return True

        if EntryRules.is_blocked(self.url):
            return True

        p = UrlLocation(self.url)
        domain_only = p.get_domain_only()

        if BlockEntry.is_blocked(domain_only):
            return True

        if not self.is_url_valid():
            return True

    def __str__(self):
        return "{}".format(self.options)

    def ping(url):
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0"

        headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Charset": "utf-8,ISO-8859-1;q=0.7,*;q=0.3",
            "Accept-Encoding": "none",
            "Accept-Language": "en-US,en;q=0.8",
            "Connection": "keep-alive",
        }

        try:
            with requests.get(
                url=url,
                headers = headers,
                timeout=20,
                verify=False,
                stream=True,
            ) as response:
                # print("UrlHandler: status_code:{}".format(response.status_code))
                if response.status_code >= 200 and response.status_code < 404:
                    return True
                else:
                    return False

        except Exception as E:
            print("UrlHandler:" + str(E))
            return False

    def get_cleaned_link(url):
        u = Url(url)
        urls_data = u.get_urls()
        return urls_data["link"]

    def is_remote_server_down(self):
        config_entry = Configuration.get_object().config_entry
        if config_entry.remote_webtools_server_location:
            request_server = RemoteServer(config_entry.remote_webtools_server_location)

            if not UrlHandlerEx.ping(config_entry.remote_webtools_server_location):
                return True
