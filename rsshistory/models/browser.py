import json

from django.db import models
from django.conf import settings

from ..webtools import WebConfig
from .system import AppLogging

from ..apps import LinkDatabase
from .entries import LinkDataModel


def get_browser_choices():
    result = []

    browsers = WebConfig.get_browsers()
    for browser in browsers:
        result.append((browser, browser))

    return result


class Browser(models.Model):
    EMPTY_FORM = -1
    AUTO = -2

    enabled = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)

    name = models.CharField(default="", max_length=2000)
    crawler = models.CharField(choices=get_browser_choices(), max_length=2000)

    settings = models.CharField(
        max_length=2000, blank=True
    )  # json map inside. script path, port etc

    class Meta:
        ordering = ["-enabled", "priority", "name"]

    def save(self, *args, **kwargs):
        browsers = WebConfig.get_browsers()
        if self.crawler not in browsers:
            AppLogging.error(
                "Cannot add crawler {}, since it is not supported by webtools".format(
                    self.crawler
                )
            )
            return

        super().save(*args, **kwargs)

    def read_browser_setup():
        """
        Reads default WebConfig browser config, and applies it to model
        """
        # Browser.objects.all().delete()

        start_index = Browser.objects.all().count()

        mapping = WebConfig.get_init_crawler_config()
        for index, browser_config in enumerate(mapping):
            settings = {}
            try:
                settings = json.dumps(browser_config["settings"])
            except ValueError as E:
                AppLogging.exc(E, "Cannot dumps browser settings")

            enabled = browser_config["enabled"]

            browsers = Browser.objects.filter(name=browser_config["name"])
            if browsers.count() == 0:
                conf = Browser.objects.create(
                    enabled=enabled,
                    name=browser_config["name"],
                    crawler=browser_config["crawler"].__name__,
                    priority=start_index + index,
                    settings=settings,
                )

    def get_browser_setup():
        """
        sets WebConfig browser config according to model
        """
        browser_mapping = []
        for browser in Browser.objects.all():
            if not browser.enabled:
                continue

            browser_config = browser.get_setup()
            if "enabled" in browser_config:
                del browser_config["enabled"]

            browser_mapping.append(browser_config)

        return browser_mapping

    def get_setup(self, string=False):
        settings = {}
        if self.settings != None and self.settings != "":
            try:
                settings = json.loads(self.settings)
            except ValueError as E:
                AppLogging.exc(E, "Cannot load browser settings")

        if string:
            crawler = self.crawler
        else:
            crawler = Browser.get_crawler_from_string(self.crawler)

        browser_config = {
            "crawler": crawler,
            "name": self.name,
            "priority": self.priority,
            "settings": settings,
        }

        return browser_config

    def prio_up(self):
        browsers = Browser.objects.all()

        if self.priority == 0:
            return

        other_browsers = Browser.objects.filter(priority=self.priority - 1)
        if other_browsers.exists():
            for other_browser in other_browsers:
                other_browser.priority = self.priority
                other_browser.save()

        self.priority -= 1
        self.save()

    def prio_down(self):
        browsers = Browser.objects.all()

        if self.priority > browsers.count():
            return

        other_browsers = Browser.objects.filter(priority=self.priority + 1)
        if other_browsers.exists():
            for other_browser in other_browsers:
                other_browser.priority = self.priority
                other_browser.save()

        self.priority += 1
        self.save()

    def get_crawler_from_string(crawler_string):
        return WebConfig.get_crawler_from_string(crawler_string)

    def __str__(self):
        return "{}".format(
            self.name,
        )
