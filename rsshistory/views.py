from pathlib import Path

from django.shortcuts import render
from django.views import generic
from django.urls import reverse

from .models import UserConfig, ConfigurationEntry
from .basictypes import *
from .configuration import Configuration
from .apps import LinkDatabase
from .configuration import Configuration
from .pluginurl.urlhandler import UrlHandler
from .webtools import HtmlPage, RssPage


class ViewPage(object):
    def __init__(self, request):
        self.request = request
        self.context = ViewPage.get_context(request)
        self.access_type = None

    def init_context(request, context):
        c = Configuration.get_object()
        context.update(c.get_context())

        if "page_description" not in context:
            if "app_description" in context:
                context["page_description"] = context["app_description"]

        context["user_config"] = UserConfig.get(request.user)

        context["is_mobile"] = ViewPage.is_mobile(request)

        return context

    def is_mobile(request):
        from django_user_agents.utils import get_user_agent

        user_agent = get_user_agent(request)
        return user_agent.is_mobile

    def get_context(request=None):
        context = {}
        context = ViewPage.init_context(request, context)
        return context

    def set_title(self, title):
        self.context["page_title"] += " - {}".format(title)

    def set_access(self, access_type):
        self.access_type = access_type

        return self.check_access()

    def set_variable(self, variable_name, variable_value):
        self.context[variable_name] = variable_value

    def check_access(self):
        if self.access_type:
            if (
                self.access_type == ConfigurationEntry.ACCESS_TYPE_OWNER
                and not self.request.user.is_superuser
            ):
                return self.render_implementation("missing_rights.html", 500)
            if (
                self.access_type == ConfigurationEntry.ACCESS_TYPE_STAFF
                and not self.request.user.is_staff
            ):
                return self.render_implementation("missing_rights.html", 500)
            if (
                self.access_type == ConfigurationEntry.ACCESS_TYPE_LOGGED
                and not self.request.user.is_authenticated
            ):
                return self.render_implementation("missing_rights.html", 500)

        config = Configuration.get_object().config_entry
        if (
            config.access_type == ConfigurationEntry.ACCESS_TYPE_OWNER
            and not self.request.user.is_superuser
        ):
            return self.render_implementation("missing_rights.html", 500)
        if (
            config.access_type == ConfigurationEntry.ACCESS_TYPE_LOGGED
            and not self.request.user.is_authenticated
        ):
            return self.render_implementation("missing_rights.html", 500)

    def get_full_template(template):
        return Path(LinkDatabase.name) / template

    def render_implementation(self, template, status_code=200):
        if self.context is None:
            self.context = self.get_context(self.request)

        return render(self.request, Path(LinkDatabase.name) / template, self.context, status=status_code)

    def render(self, template):
        result = self.check_access()
        if result is not None:
            return result

        return self.render_implementation(template)

    def fill_context_type(context, url):
        handler = UrlHandler.get_type(url)

        context["is_youtube_video"] = type(handler) == UrlHandler.youtube_video_handler
        context["is_youtube_channel"] = type(handler) == UrlHandler.youtube_channel_handler
        context["is_odysee_video"] = type(handler) == UrlHandler.odysee_video_handler
        context["is_odysee_channel"] = type(handler) == UrlHandler.odysee_channel_handler
        context["is_html"] = type(handler) == HtmlPage
        context["is_rss"] = type(handler) == RssPage


def index(request):
    p = ViewPage(request)
    p.set_title("Index")
    return p.render("index.html")
