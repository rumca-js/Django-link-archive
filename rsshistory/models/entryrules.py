"""
Defined by user, by GUI
"""

from django.db import models

from ..webtools import (
    UrlLocation,
)

from .entries import LinkDataModel
from .browser import Browser
from .system import AppLogging
from ..apps import LinkDatabase


class EntryRules(models.Model):
    enabled = models.BooleanField(default=True)

    rule_name = models.CharField(max_length=1000, blank=True, help_text="Rule name")

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

    trigger_text_hits = models.IntegerField(default=1)

    block = models.BooleanField(
        default=False,
        help_text="Blocks entry",
    )

    auto_tag = models.CharField(
        max_length=1000, blank=True, help_text="Automatically tag"
    )

    apply_age_limit = models.IntegerField(blank=True, null=True)

    browser = models.ForeignKey(
        Browser,
        on_delete=models.SET_NULL,
        related_name="browser_rules",
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["-enabled", "rule_name"]

    def is_valid(self):
        if self.browser:
            if not self.browser.is_valid():
                return False

        return True

    def get_rule_urls(self):
        result = set()

        urls = self.trigger_rule_url.split(",")
        for url in urls:
            result.add(url.strip())

        return result

    def get_url_rules(url):
        result = []

        rules = EntryRules.objects.filter(enabled=True)
        for rule in rules:
            rule_urls = rule.get_rule_urls()
            for rule_url in rule_urls:
                if url.find(rule_url) >= 0:
                    result.append(rule)

        return result

    def is_url_blocked(url):
        from .blockentry import BlockEntry

        rules = EntryRules.objects.filter(block=True, enabled=True)
        for rule in rules:
            rule_urls = rule.get_rule_urls()
            for rule_url in rule_urls:
                if rule_url != "":
                    if url.find(rule_url) >= 0:
                        return True

        p = UrlLocation(url)
        domain_only = p.get_domain_only()

        if BlockEntry.is_blocked(domain_only):
            return True

        return False

    def is_url_blocked_by_rule(self, url):
        rule_urls = self.get_rule_urls()
        for rule_url in rule_urls:
            if url.find(rule_url) >= 0:
                return True

        return False

    def get_entry_pulp(entry):
        pulp = str(entry.title) + str(entry.description)

        # ignore case
        return pulp.lower()

    def is_text_triggered(self, text):
        sum = 0

        trigger_texts = self.trigger_text
        trigger_split = trigger_texts.split(",")

        for trigger_text in trigger_split:
            # ignore case
            trigger_text = trigger_text.lower()

            sum += text.count(trigger_text)

        if sum >= self.trigger_text_hits:
            return True

        return False

    def is_blocked_by_text(text):
        rules = EntryRules.objects.filter(enabled=True, block=True).exclude(trigger_text = "")
        for rule in rules:
            if rule.is_text_triggered(text):
                return True

        return False

    def is_entry_blocked(entry):
        if EntryRules.is_url_blocked(entry.link):
            return True

        text = EntryRules.get_entry_pulp(entry)
        return EntryRules.is_blocked_by_text(text)

    def apply_entry_rule(entry):
        if EntryRules.is_url_blocked(entry.link):
            entry.delete()
            return

        EntryRules.check_entry_text_rules(entry)

    def get_dict_pulp(dictionary):
        title = ""
        if "title" in dictionary:
            title = dictionary["title"]
        description = ""
        if "description" in dictionary:
            description = dictionary["description"]

        pulp = str(title) + str(description)

        # ignore case
        return pulp.lower()

    def get_age_for_dictionary(dictionary):
        text = EntryRules.get_dict_pulp(dictionary)

        age = None

        rules = EntryRules.objects.filter(enabled=True, apply_age_limit__gt = 0).exclude(trigger_text = "")
        for rule in rules:
            if rule.is_text_triggered(text):
                if not age:
                    age = rule.apply_age_limit
                elif rule.apply_age_limit:
                    if age < rule.apply_age_limit:
                        age = rule.apply_age_limit

        return age

    def check_entry_text_rules(entry):
        text = EntryRules.get_entry_pulp(entry)

        rules = EntryRules.objects.filter(enabled=True).exclude(trigger_text = "")
        for rule in rules:
            if rule.is_text_triggered(text):
                rule.apply_entry_rule_action(entry)

    def apply_entry_rule_action(self, entry):
        if self.block:
            entry.delete()
        if self.apply_age_limit:
            if not entry.age or entry.age < self.apply_age_limit:
                entry.age = self.apply_age_limit
                entry.save()

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
