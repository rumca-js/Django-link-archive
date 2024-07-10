from django.db import models

from .entries import LinkDataModel
from .system import AppLogging

from ..apps import LinkDatabase


class EntryRules(models.Model):
    enabled = models.BooleanField(default=True)

    rule_url = models.CharField(max_length=1000)  # url syntax

    rule_name = models.CharField(max_length=1000, blank=True, help_text="Rule name")

    block = models.BooleanField(
        default=False,
        help_text="Blocks entry",
    )

    auto_tag = models.CharField(
        max_length=1000, blank=True, help_text="Automatically tag"
    )

    requires_headless = models.BooleanField(
        default=False,
        help_text="Requires headless browser",
    )

    requires_full_browser = models.BooleanField(
        default=False,
        help_text="Requires full browser setup",
    )

    def get_rule_urls(self):
        result = set()

        urls = self.rule_url.split(",")
        for url in urls:
            result.add(url.strip())

        return result

    def is_blocked(url):
        rules = EntryRules.objects.filter(block=True, enabled=True)
        for rule in rules:
            rule_urls = rule.get_rule_urls()
            for rule_url in rule_urls:
                if url.find(rule_url) >= 0:
                    return True

        return False

    def is_headless_browser_required(url):
        rules = EntryRules.objects.filter(requires_headless=True, enabled=True)
        for rule in rules:
            rule_urls = rule.get_rule_urls()
            for rule_url in rule_urls:
                if url.find(rule_url) >= 0:
                    return True

        return False

    def is_full_browser_required(url):
        rules = EntryRules.objects.filter(requires_full_browser=True, enabled=True)
        for rule in rules:
            rule_urls = rule.get_rule_urls()
            for rule_url in rule_urls:
                if url.find(rule_url) >= 0:
                    return True

        return False
