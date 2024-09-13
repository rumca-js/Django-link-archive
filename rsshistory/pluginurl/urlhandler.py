import traceback

from webtools import Url, DomainAwarePage, UrlPropertyValidator

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

    def __init__(self, url=None, page_object=None, page_options=None):
        super().__init__(url, page_object=page_object, page_options=page_options)

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

    def get_init_page_options(self, init_options=None):
        o = super().get_init_page_options(init_options)

        if UrlHandler.is_full_browser_required(self.url):
            o.use_full_browser = True
        if UrlHandler.is_headless_browser_required(self.url):
            o.use_headless_browser = True

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
