import traceback

from ..webtools import Url, DomainAwarePage, UrlPropertyValidator

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

    def __init__(self, url=None, page_options=None, handler_class=None):
        super().__init__(url, page_options=page_options, handler_class=handler_class)
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

        p = DomainAwarePage(self.url)
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
