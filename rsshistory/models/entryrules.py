
from django.db import models

from .entries import LinkDataModel
from .system import AppLogging

from ..apps import LinkDatabase


class EntryRule(models.Model):
    enabled = models.BooleanField(default=True)

    rule_url = models.CharField(max_length=1000) # url syntax

    rule_name = models.CharField(
        max_length=1000,
        blank=True,
        help_text="Rule name")

    block = models.BooleanField(
        default=False,
        help_text="Blocks entry",
    )

    auto_tag = models.CharField(
        max_length=1000,
        blank=True,
        help_text="Automatically tag")

    requires_selenium = models.BooleanField(
        default=False,
        help_text="Requires selenium",
    )

    requires_selenium_full = models.BooleanField(
        default=False,
        help_text="Requires full selenium setup",
    )

    def add_default():
        """
        Creates default, sane rules
        """
        pass

    def get_blocked_urls():
        block_urls = set()

        rules = EntryRule.objects.all()
        for rule in rules:
            if not rule.block:
                continue

            urls = rule.rule_url.split(",")
            for url in urls:
                block_urls.add(url.strip())

        print(block_urls)

        return list(block_urls)
