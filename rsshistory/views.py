from pathlib import Path

from django.shortcuts import render
from django.views import generic
from django.urls import reverse

from .models import UserConfig, ConfigurationEntry
from .controllers import (
    SourceDataController,
    LinkDataController,
    ArchiveLinkDataController,
)
from .basictypes import *
from .configuration import Configuration
from .apps import LinkDatabase


class ContextData(object):
    # https://stackoverflow.com/questions/66630043/django-is-loading-template-from-the-wrong-app
    app_name = Path(LinkDatabase.name)

    def get_full_template(template):
        return ContextData.app_name / template

    def init_context(request, context):
        c = Configuration.get_object()
        context.update(c.get_context())

        user_name = request.user.get_username()
        context["user_config"] = UserConfig.get(user_name)

        from django_user_agents.utils import get_user_agent

        user_agent = get_user_agent(request)
        context["is_mobile"] = user_agent.is_mobile

        return context

    def get_context(request=None):
        context = {}
        context = ContextData.init_context(request, context)
        return context

    def render(request, template, context=None):
        if context is None:
            context = self.get_context(request)

        return render(request, ContextData.app_name / template, context)


class ViewPage(object):
    def __init__(self, request):
        self.request = request
        self.context = ContextData.get_context(request)
        self.access_type = None

    def set_title(self, title):
        self.context["page_title"] += " - {}".format(title)

    def set_access(self, access_type):
        self.access_type = access_type

        return self.check_access()

    def set_variable(self, variable_name, variable_value):
        self.context[variable_name] = variable_value

    def check_access(self):
        if self.access_type:
            if self.access_type == ConfigurationEntry.ACCESS_TYPE_OWNER and not self.request.user.is_superuser:
                return ContextData.render(self.request, "missing_rights.html", self.context)
            if self.access_type == ConfigurationEntry.ACCESS_TYPE_STAFF and not self.request.user.is_staff:
                return ContextData.render(self.request, "missing_rights.html", self.context)
            if self.access_type == ConfigurationEntry.ACCESS_TYPE_LOGGED and not self.request.user.is_authenticated:
                return ContextData.render(self.request, "missing_rights.html", self.context)

        config = ConfigurationEntry.get()
        if config.access_type == ConfigurationEntry.ACCESS_TYPE_OWNER and not self.request.user.is_superuser:
            return ContextData.render(self.request, "missing_rights.html", self.context)
        if config.access_type == ConfigurationEntry.ACCESS_TYPE_LOGGED and not self.request.user.is_authenticated:
            return ContextData.render(self.request, "missing_rights.html", self.context)

    def render(self, template):
        result = self.check_access()
        if result is not None:
            return result

        return ContextData.render(self.request, template, self.context)


def index(request):
    p = ViewPage(request)
    p.set_title("Index")
    return p.render("index.html")
