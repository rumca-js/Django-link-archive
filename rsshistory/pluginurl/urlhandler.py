import traceback

from ..webtools import Url, DomainAwarePage, UrlPropertyValidator

from ..apps import LinkDatabase
from ..models import AppLogging, EntryRules
from ..configuration import Configuration


class UrlHandler(Url):
    """
    Provides handler, controller for a link. Should inherit title & description API, just like
    webtools Url.

    You can extend it, provide more handlers.

    The controller job is to provide usefull information about link.
    """

    def __init__(self, url=None, page_options=None):
        super().__init__(url, page_options=page_options)
        self.url_builder = UrlHandler

        if not url or url == "":
            lines = traceback.format_stack()
            line_text = ""
            for line in lines:
                line_text += line

            AppLogging.error(
                "Invalid use of UrlHandler API {};Lines:{}".format(url, line_text)
            )

            return

    def is_headless_browser_required(url):
        if EntryRules.is_headless_browser_required(url):
            return True

        if Url.is_headless_browser_required(url):
            return True

        return False

    def is_full_browser_required(url):
        if EntryRules.is_full_browser_required(url):
            return True

        if Url.is_full_browser_required(url):
            return True

        return False

    def get_init_page_options(self, url, init_options=None):
        o = super().get_init_page_options(url, init_options)

        # TODO this is reading overhead. We might cache something?
        from ..models import Browser
        o.mode_mapping = Browser.get_browser_setup()

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

        if not self.is_url_valid():
            return True

    def is_url_valid(self):
        if not super().is_url_valid():
            return False

        return True

    def __str__(self):
        return "{}".format(self.options)
