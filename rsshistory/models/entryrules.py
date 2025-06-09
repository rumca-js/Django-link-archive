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
        max_length=1000, blank=True, help_text="New entries can added using colon"
    )  # url syntax

    trigger_text = models.CharField(
        max_length=1000,
        blank=True,
        help_text="Text that triggers the rule",
    )

    trigger_text_hits = models.IntegerField(default=1)

    trigger_text_fields = models.CharField(
        max_length=1000,
        blank=True,
        help_text="fields that will be used for rule triggering. If not set, then title and description are used.",
    )  # url syntax

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
        ordering = [
            "-enabled",
            "block",
            "browser",
            "apply_age_limit",
            "auto_tag",
            "rule_name",
        ]

    def is_valid(self):
        if self.browser:
            if not self.browser.is_valid():
                return False

        return True

    def get_rule_urls(self):
        """
        Returns list of urls handled by this rule
        """
        result = set()

        urls = self.trigger_rule_url.split(",")
        for url in urls:
            stripped = url.strip()
            if stripped != "":
                result.add(stripped)

        return result

    def get_trigger_texts(self):
        result = set()

        trigger_texts = self.trigger_text
        trigger_split = trigger_texts.split(",")

        for trigger_text in trigger_split:
            stripped = trigger_text.strip()
            if stripped != "":
                result.add(stripped)

        return result

    def get_trigger_fields(self):
        if not self.trigger_text_fields or self.trigger_text_fields == "":
            return ["title", "description"]

        if "," not in self.trigger_text_fields:
            return [self.trigger_text_fields.strip()]

        fields = [field.strip() for field in self.trigger_text_fields.split(",")]
        return fields

    def is_url_triggering(self, url):
        rule_urls = self.get_rule_urls()
        for rule_url in rule_urls:
            if url.find(rule_url) >= 0:
                return True

        return False

    def get_entry_pulp(self, entry):
        pulp = ""

        fields = self.get_trigger_fields()

        if "title" in fields:
            pulp += str(entry.title)

        if "description" in fields:
            pulp += str(entry.description)

        # ignore case
        return pulp.lower()

    def get_dict_pulp(self, dictionary):
        pulp = ""

        fields = self.get_trigger_fields()

        if "title" in fields:
            if "title" in dictionary:
                pulp += str(dictionary["title"])

        if "description" in fields:
            if "description" in dictionary:
                pulp += str(dictionary["description"])

        if "contents" in fields:
            if "contents" in dictionary:
                pulp += str(dictionary["contents"])

        # ignore case
        return pulp.lower()

    def is_text_triggered(self, text):
        sum = 0

        trigger_split = self.get_trigger_texts()

        for trigger_text in trigger_split:
            # ignore case
            trigger_text = trigger_text.lower()
            trigger_text = trigger_text.strip()

            if trigger_text != "":
                sum += text.count(trigger_text)

        if sum >= self.trigger_text_hits:
            return True

        return False

    def check_rule(self, entry):
        p = UrlLocation(entry.link)
        domain_only = p.get_domain_only()

        if self.is_url_triggering(domain_only):
            if self.block:
                if self.apply_entry_rule_action(entry):
                    return True

        text = self.get_entry_pulp(entry)
        if self.is_text_triggered(text):
            if self.apply_entry_rule_action(entry):
                return True

    def apply_entry_rule_action(self, entry):
        if self.block:
            EntryRules.attemp_delete(entry, self)
            return True

        if self.apply_age_limit:
            if not entry.age or entry.age < self.apply_age_limit:
                entry.age = self.apply_age_limit
                entry.save()

        return False

    def get_url_rules(url):
        result = []

        rules = EntryRules.objects.filter(enabled=True)
        for rule in rules:
            if rule.is_url_triggering(url):
                result.append(rule)

        return result

    def is_url_blocked(url):
        from .blockentry import BlockEntry

        rules = EntryRules.objects.filter(block=True, enabled=True)
        for rule in rules:
            if rule.is_url_triggering(url):
                return rule

        p = UrlLocation(url)
        domain_only = p.get_domain_only()

        block = BlockEntry.get_entry(domain_only)
        if block:
            return block

    def is_dict_blocked(dictionary):
        if "link" in dictionary:
            reason = EntryRules.is_url_blocked(dictionary["link"])
            if reason:
                return reason

        rules = EntryRules.objects.filter(enabled=True, block=True).exclude(
            trigger_text=""
        )
        for rule in rules:
            text = rule.get_dict_pulp(dictionary)
            if rule.is_text_triggered(text):
                return rule

    def is_entry_blocked(entry):
        reason = EntryRules.is_url_blocked(entry.link)
        if reason:
            return reason

        rules = EntryRules.objects.filter(enabled=True, block=True).exclude(
            trigger_text=""
        )
        for rule in rules:
            text = rule.get_entry_pulp(entry)
            if rule.is_text_triggered(text):
                return rule

    def check_all(entry):
        """
        @returns True if entry is deleted
        """
        for rule in EntryRules.objects.filter(enabled=True):
            if rule.check_rule(entry):
                return True

    def attemp_delete(entry, entry_rule=None):
        if not entry.is_removable():
            return

        from ..configuration import Configuration

        if Configuration.get_object().config_entry.log_remove_entries:
            if entry_rule:
                AppLogging.info("Removing entry:{} rule ID:{}".format(entry.id, entyry_rule.id))
            else:
                AppLogging.info("Removing entry:{}".format(entry.id))

        entry.delete()

    def get_age_for_dictionary(dictionary):
        age = None

        rules = EntryRules.objects.filter(enabled=True, apply_age_limit__gt=0).exclude(
            trigger_text=""
        )
        for rule in rules:
            text = rule.get_dict_pulp(dictionary)
            if rule.is_text_triggered(text):
                if not age:
                    age = rule.apply_age_limit
                elif rule.apply_age_limit:
                    if age < rule.apply_age_limit:
                        age = rule.apply_age_limit

        return age

    def check_entry_text_rules(entry):
        rules = EntryRules.objects.filter(enabled=True).exclude(trigger_text="")
        for rule in rules:
            text = rule.get_entry_pulp(entry)
            if rule.is_text_triggered(text):
                rule.apply_entry_rule_action(entry)

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

    def initialize_common_rules():
        EntryRules.objects.create(
            rule_name="casinos-block",
            trigger_text="casino, lotter, jackpot, bingo, poker, slot, betting, togel, gacor, bandar judi, pagcor, slotlara kadar, canli bahis, terpopuler, deposit, g2gbet, terpercaya, maxtoto, Gampang, bonus giveaway, pg slot, cashback rewards, situs slot, slot situs",
            block=True,
        )

        EntryRules.objects.create(
            rule_name="sexual-block",
            trigger_text="mastubat, porn, sexseite, zoophilia, chaturbat",
            block=True,
        )

        EntryRules.objects.create(
            rule_name="inactive-links",
            trigger_text="forbidden, access denied, page not found, site not found, 404 not found, 404: not found, error 404, 404 error, 404 page, 404 file not found, squarespace - website expired, domain name for sale, account suspended, the request could not be satisfied",
            trigger_text_fields="title",
            block=True,
        )

    def __str__(self):
        return "EntryRule ID:{}, Name:{}".format(self.id, self.rule_name)
