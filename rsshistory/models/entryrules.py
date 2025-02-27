"""
Defined by user, by GUI
"""

from django.db import models

from .entries import LinkDataModel
from .browser import Browser
from .system import AppLogging
from ..apps import LinkDatabase


class EntryRules(models.Model):
    enabled = models.BooleanField(default=True)

    trigger_rule_url = models.CharField(
        max_length=1000,
        blank=True,
        help_text="New entries can added using colon"
    )  # url syntax

    trigger_text = models.CharField(
        max_length=1000,
        blank = True,
        help_text="Text that triggers the rule",
    )

    rule_name = models.CharField(max_length=1000, blank=True, help_text="Rule name")

    block = models.BooleanField(
        default=False,
        help_text="Blocks entry",
    )

    auto_tag = models.CharField(
        max_length=1000, blank=True, help_text="Automatically tag"
    )

    browser = models.ForeignKey(
        Browser,
        on_delete=models.SET_NULL,
        related_name="browser_rules",
        blank=True,
        null=True,
    )

    def get_rule_urls(self):
        result = set()

        urls = self.trigger_rule_url.split(",")
        for url in urls:
            result.add(url.strip())

        return result

    def is_blocked(url):
        rules = EntryRules.objects.filter(block=True, enabled=True)
        for rule in rules:
            rule_urls = rule.get_rule_urls()
            for rule_url in rule_urls:
                if rule_url != "":
                    if url.find(rule_url) >= 0:
                        return True

        return False

    def is_valid(self):
        if self.browser:
            if not self.browser.is_valid():
                return False

        return True

    def is_blocked_by_rule(self, url):
        rule_urls = self.get_rule_urls()
        for rule_url in rule_urls:
            if url.find(rule_url) >= 0:
                return True

        return False

    def is_entry_blocked(entry):
        if EntryRules.is_blocked(entry.link):
            return True

        pulp = str(entry.title) + str(entry.description)
        pulp = pulp.lower()

        if EntryRules.is_blocked_by_text(pulp):
            return True

        return False

    def is_blocked_by_text(text):
        sum = 0

        # ignore case
        text = text.lower()

        rules = EntryRules.objects.filter(block=True, enabled=True).exclude(trigger_text = "")
        for rule in rules:
            trigger_texts = rule.trigger_text
            trigger_split = trigger_texts.split(",")

            for trigger_text in trigger_split:
                # ignore case
                trigger_text = trigger_text.lower()

                sum += text.count(trigger_text)

        return sum > 3

    def get_url_rules(url):
        result = []

        rules = EntryRules.objects.filter(enabled=True)
        for rule in rules:
            rule_urls = rule.get_rule_urls()
            for rule_url in rule_urls:
                if url.find(rule_url) >= 0:
                    result.append(rule)

        return result

    def update_link_service_rule():
        name = "link service"
        link_services = EntryRules.objects.filter(rule_name=name)
        if link_services.exists():
            link_service = link_services[0]
        else:
            link_service = EntryRules.objects.create(rule_name=name)

        link_service.link_url = ".bit.ly"
        link_service.block = True
        link_service.save()

    def update_link_service_rule():
        name = "web spam"
        link_services = EntryRules.objects.filter(rule_name=name)
        if link_services.exists():
            link_service = link_services[0]
        else:
            link_service = EntryRules.objects.create(rule_name=name)

        link_service.link_url = (
            ".shoparena.pl, .ascii.uk, .bestbuenosaireshotels.com, .itch.io"
        )
        link_service.block = True
        link_service.save()
