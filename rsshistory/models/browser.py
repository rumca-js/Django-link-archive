import json

from django.db import models
from django.conf import settings

from ..webtools import WebConfig
from .system import AppLogging

from ..apps import LinkDatabase
from .entries import LinkDataModel


class BrowserMode(models.Model):
    mode = models.CharField(max_length=2000, unique=True)

    def get_modes():
        modes = BrowserMode.objects.all()
        modes = modes.values_list("mode", flat=True)
        return modes


def get_browser_choices():
    result = []

    browsers = WebConfig.get_browsers()
    for browser in browsers:
        result.append((browser, browser))

    return result


class Browser(models.Model):
    enabled = models.BooleanField(default=True)

    mode = models.ForeignKey(
        BrowserMode,
        on_delete=models.CASCADE,
        related_name="browsers",
    )

    crawler = models.CharField(choices=get_browser_choices(), max_length=2000)

    settings = models.CharField(
        max_length=2000, blank=True
    )  # json map inside. script path, port etc

    class Meta:
        ordering = ["-enabled", "mode"]

    def save(self, *args, **kwargs):
        browsers = WebConfig.get_browsers()
        if self.crawler not in browsers:
            return

        super().save(*args, **kwargs)

    def read_browser_setup():
        """
        Reads default WebConfigs browser config, and applies it to model
        """
        BrowserMode.objects.all().delete()
        Browser.objects.all().delete()

        mapping = WebConfig.get_init_crawler_config()
        for mode_name in mapping:
            mode_browser_config = mapping[mode_name]

            modes = BrowserMode.objects.filter(mode=mode_name)
            if not modes.exists():
                mode = BrowserMode.objects.create(mode=mode_name)

            index = 0
            for browser_config in mode_browser_config:
                settings = {}
                try:
                    settings = json.dumps(browser_config["settings"])
                except ValueError as E:
                    AppLogging.exc(E, "Cannot dumps browser settings")

                enabled = browser_config["enabled"]

                conf = Browser.objects.create(
                    enabled=enabled,
                    mode=mode,
                    crawler=browser_config["crawler"],
                    settings=settings,
                )
                index += 1

    def get_browser_setup():
        """
        sets WebConfigs browser config according to model
        """
        browser_mapping = {}
        for browser in Browser.objects.all():
            mode = browser.mode.mode
            if mode not in browser_mapping:
                browser_mapping[mode] = []

            if not browser.enabled:
                continue

            settings = {}
            if browser.settings != None and browser.settings != "":
                try:
                    settings = json.loads(browser.settings)
                except ValueError as E:
                    AppLogging.exc(E, "Cannot load browser settings")

            browser_config = {
                "crawler": browser.crawler,
                "settings": settings,
            }

            browser_mapping[mode].append(browser_config)

        return browser_mapping
