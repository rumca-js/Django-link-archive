from pathlib import Path

from django.shortcuts import render
from django.views import generic
from django.urls import reverse

from webtools import HtmlPage, RssPage, HttpPageHandler

from .models import UserConfig, ConfigurationEntry, AppLogging, ApiKeys
from .configuration import Configuration
from .apps import LinkDatabase
from .configuration import Configuration
from .pluginurl.urlhandler import UrlHandler


def get_search_term_request(request):
    search_term = ""
    if "title" in request.GET and request.GET["title"] != "":
        search_term = request.GET["title"]
    elif "tag" in request.GET and request.GET["tag"] != "":
        search_term = request.GET["tag"]
    elif "search_history" in request.GET and request.GET["search_history"] != "":
        search_term = request.GET["search_history"]
    elif "search" in request.GET and request.GET["search"] != "":
        search_term = request.GET["search"]

    return search_term


def get_request_order_by(request):
    if "order" in request.GET:
        order = request.GET["order"]
        return [order]
    else:
        config = Configuration.get_object().config_entry
        return config.get_entries_order_by()


def get_request_page_num(request):
    if "page" in request.GET:
        page = request.GET["page"]
        try:
            page = int(page)
        except Exception as e:
            page = 1

        return page
    else:
        return 1


class ViewPage(object):
    def __init__(self, request):
        self.request = request
        self.access_type = None

        self.context = None
        self.context = self.get_context()

    def init_context(self, context):
        if self.is_user_allowed(self.access_type):
            c = Configuration.get_object()
            context.update(c.get_context())

            context["is_user_allowed"] = True
        else:
            context.update(Configuration.get_context_minimal())
            context["is_user_allowed"] = False

        if "page_description" not in context:
            if "app_description" in context:
                context["page_description"] = context["app_description"]

        context["user_config"] = UserConfig.get(self.request.user)
        context["is_mobile"] = self.is_mobile()

        return context

    def is_mobile(self):
        from django_user_agents.utils import get_user_agent

        try:
            user_agent = get_user_agent(self.request)
            return user_agent.is_mobile
        except Exception as E:
            AppLogging.exc(E, "Could not read django user agent")

            return False

    def get_context(self, request=None):
        if self.context is not None:
            return self.context

        context = {}
        context = self.init_context(context)

        self.context = context

        return context

    def set_title(self, title):
        self.context["page_title"] += " - {}".format(title)

    def set_access(self, access_type):
        self.access_type = access_type

        return self.check_access()

    def set_variable(self, variable_name, variable_value):
        self.context[variable_name] = variable_value

    def check_access(self):
        if not self.is_user_allowed(self.access_type) and not self.is_api_key_allowed():
            return self.render_implementation("missing_rights.html", 500)

    def is_api_key_allowed(self):
        key = None
        if "key" in self.request.GET and self.request.GET["key"]:
            key = self.request.GET["key"]

        if not key:
            return False

        keys = ApiKeys.objects.filter(key = key)
        if keys.exists():
            return True

    def is_user_allowed(self, access_type):
        if not self.is_user_allowed_on_page_level(self.access_type):
            return False

        if not self.is_user_allowed_on_system_level():
            return False

        return True

    def is_user_allowed_on_page_level(self, access_type):
        if (
            access_type == ConfigurationEntry.ACCESS_TYPE_OWNER
            and not self.request.user.is_superuser
        ):
            return False
        if (
            access_type == ConfigurationEntry.ACCESS_TYPE_STAFF
            and not self.request.user.is_staff
        ):
            return False
        if (
            access_type == ConfigurationEntry.ACCESS_TYPE_LOGGED
            and not self.request.user.is_authenticated
        ):
            return False

        return True

    def is_user_allowed_on_system_level(self):
        config = Configuration.get_object().config_entry
        if (
            config.access_type == ConfigurationEntry.ACCESS_TYPE_OWNER
            and not self.request.user.is_superuser
        ):
            return False
        if (
            config.access_type == ConfigurationEntry.ACCESS_TYPE_LOGGED
            and not self.request.user.is_authenticated
        ):
            return False

        return True

    def get_full_template(template):
        return Path(LinkDatabase.name) / template

    def render_implementation(self, template, status_code=200):
        return render(
            self.request,
            Path(LinkDatabase.name) / template,
            self.get_context(),
            status=status_code,
        )

    def render(self, template, status_code=200):
        result = self.check_access()
        if result is not None:
            return result

        return self.render_implementation(template, status_code)

    def fill_context_type(context, url=None, fast_check=True, urlhandler=None):
        if urlhandler is None and url:
            urlhandler = UrlHandler(url)

        context["is_youtube_video"] = (
            type(urlhandler.get_handler()) == UrlHandler.youtube_video_handler
        )
        context["is_youtube_channel"] = (
            type(urlhandler.get_handler()) == UrlHandler.youtube_channel_handler
        )
        context["is_odysee_video"] = (
            type(urlhandler.get_handler()) == UrlHandler.odysee_video_handler
        )
        context["is_odysee_channel"] = (
            type(urlhandler.get_handler()) == UrlHandler.odysee_channel_handler
        )

        if type(urlhandler.get_handler()) == HttpPageHandler:
            context["is_html"] = type(urlhandler.get_handler().p) == HtmlPage
            context["is_rss"] = type(urlhandler.get_handler().p) == RssPage
