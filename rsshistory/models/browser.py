import json

from django.db import models
from django.conf import settings

from .system import AppLogging

from ..apps import LinkDatabase
from .entries import LinkDataModel


class Browser(models.Model):
    EMPTY_FORM = -1
    AUTO = -2

    enabled = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)
    name = models.CharField(default="", max_length=2000)
    ignore_errors = models.BooleanField(default=False)

    settings = models.CharField(
        max_length=2000, blank=True
    )  # json map inside. script path, port etc

    class Meta:
        ordering = ["-enabled", "priority", "name"]

    def save(self, *args, **kwargs):
        if not self.is_valid():
            AppLogging.error(
                "Browser cannot be saved due to errors".format(self.name)
            )
            return

        super().save(*args, **kwargs)

    def is_valid(self):
        if self.settings != None and self.settings != "":
            try:
                settings = json.loads(self.settings)
            except ValueError as E:
                return False

        return True

    def read_browser_setup():
        """
        Reads configuration from the remote
        """
        from ..configuration import Configuration

        start_index = Browser.objects.all().count()

        server = Configuration.get_object().get_remote_server()
        crawlers_data = server.get_infoj()

        for index, browser_config in enumerate(crawlers_data["crawlers"]):
            settings = {}
            try:
                settings = json.dumps(browser_config["settings"])
            except ValueError as E:
                AppLogging.exc(E, "Cannot dumps browser settings")

            enabled = browser_config["enabled"]

            browsers = Browser.objects.filter(name=browser_config["name"])
            if not browsers.exists():
                conf = Browser.objects.create(
                    enabled=enabled,
                    name=browser_config["name"],
                    priority=start_index + index,
                    settings=settings,
                )

    def get_browsers():
        return Browser.objects.filter(enabled=True)

    def reset_priorities():
        browsers = list(Browser.objects.all().order_by("priority"))

        for i, browser in enumerate(browsers):
            if browser.priority != i:
                browser.priority = i
                browser.save()

    def prio_up(self):
        browsers = list(Browser.objects.all().order_by("priority"))

        index = browsers.index(self)
        if index == 0:
            return

        browsers[index], browsers[index - 1] = browsers[index - 1], browsers[index]

        for i, browser in enumerate(browsers):
            if browser.priority != i:
                browser.priority = i
                browser.save()

    def prio_down(self):
        browsers = list(Browser.objects.all().order_by("priority"))

        index = browsers.index(self)

        if index == len(browsers) - 1:
            return

        browsers[index], browsers[index + 1] = browsers[index + 1], browsers[index]

        for i, browser in enumerate(browsers):
            if browser.priority != i:
                browser.priority = i
                browser.save()

    def __str__(self):
        return "{}".format(
            self.name,
        )
