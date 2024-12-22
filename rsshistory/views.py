from pathlib import Path
from urllib.parse import unquote

from django.shortcuts import render, redirect
from django.views import generic
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.http import urlencode

from .webtools import HtmlPage, RssPage, HttpPageHandler

from .models import (
    UserConfig,
    ConfigurationEntry,
    AppLogging,
    ApiKeys,
)
from .apps import LinkDatabase
from .configuration import Configuration
from .pluginurl.urlhandler import UrlHandler


def get_search_term(themap):
    search_term = ""
    if "title" in themap and themap["title"] != "":
        search_term = themap["title"]
    elif "tag" in themap and themap["tag"] != "":
        search_term = themap["tag"]
    elif "search_history" in themap and themap["search_history"] != "":
        search_term = themap["search_history"]
    elif "search" in themap and themap["search"] != "":
        search_term = themap["search"]
        if search_term[0] == "'":
            search_term = search_term[1:-1]
        if search_term[0] == '"':
            search_term = search_term[1:-1]

        search_term = unquote(search_term)

    return search_term


def get_order_by(themap):
    if "order" in themap:
        order = themap["order"]
        return [order]
    else:
        config = ConfigurationEntry.get()
        return config.get_entries_order_by()


def get_page_num(themap):
    if "page" in themap:
        page = themap["page"]
        try:
            page = int(page)
        except ValueError:
            page = 1

        return page
    else:
        return 1


class ViewPage(object):
    def __init__(self, request):
        self.request = request
        self.view_access_type = None

        self.context = None
        self.context = self.get_context()
        self.is_mobile = self.read_mobile_status()

    def init_context(self, context):
        from .models import (
            ReadLater,
        )
        from .controllers import BackgroundJobController

        c = Configuration.get_object()
        config = ConfigurationEntry.get()

        context["debug"] = config.debug_mode

        if self.is_user_allowed(self.view_access_type) and config.enable_background_jobs:
            context.update(c.get_context())

            context["is_user_allowed"] = True

        else:
            context.update(Configuration.get_context_minimal())
            # to not logged users indicate everything is fine and dandy

            context["is_user_allowed"] = False

        if "page_description" not in context:
            if "app_description" in context:
                context["page_description"] = context["app_description"]

        if self.request:
            context["user_config"] = UserConfig.get_or_create(self.request.user)
        else:
            context["user_config"] = UserConfig.get()

        context["config"] = ConfigurationEntry.get()
        context["view"] = self

        return context

    def read_mobile_status(self):
        from django_user_agents.utils import get_user_agent

        try:
            user_agent = get_user_agent(self.request)
            return user_agent.is_mobile
        except Exception as E:
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

    def set_access(self, view_access_type):
        self.view_access_type = view_access_type

        return self.check_access()

    def set_variable(self, variable_name, variable_value):
        self.context[variable_name] = variable_value

    def check_access(self):
        if not self.is_user_allowed(self.view_access_type) and not self.is_api_key_allowed():
            return self.render_implementation("missing_rights.html", 500)

    def is_api_key_allowed(self):
        key = None
        if "key" in self.request.GET and self.request.GET["key"]:
            key = self.request.GET["key"]

        if not key:
            return False

        keys = ApiKeys.objects.filter(key=key)
        if keys.exists():
            return True

    def is_user_allowed(self, view_access_type):
        if not self.is_user_allowed_on_page_level(self.view_access_type):
            return False

        if not self.is_user_allowed_on_system_level():
            return False

        return True

    def is_user_allowed_on_page_level(self, view_access_type):
        if not self.request:
            return False

        if (
            view_access_type == ConfigurationEntry.ACCESS_TYPE_OWNER
            and not self.request.user.is_superuser
        ):
            return False
        if (
            view_access_type == ConfigurationEntry.ACCESS_TYPE_STAFF
            and not self.request.user.is_staff
        ):
            return False
        if (
            view_access_type == ConfigurationEntry.ACCESS_TYPE_LOGGED
            and not self.request.user.is_authenticated
        ):
            return False

        return True

    def is_user_allowed_on_system_level(self):
        if not self.request:
            return False

        config = ConfigurationEntry.get()
        if (
            config.view_access_type == ConfigurationEntry.ACCESS_TYPE_OWNER
            and not self.request.user.is_superuser
        ):
            return False
        if (
            config.view_access_type == ConfigurationEntry.ACCESS_TYPE_LOGGED
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

    def get_pagination_args(self):
        infilters = self.request.GET

        filter_data = {}
        for key in infilters:
            value = infilters[key]
            if key != "page" and value != "":
                filter_data[key] = value
        return "&" + urlencode(filter_data)

    def get_page_num(self):
        themap = self.request.GET

        if "page" in themap:
            page = themap["page"]
            try:
                page = int(page)
            except ValueError:
                page = 1

            return page
        else:
            return 1


class GenericListView(generic.ListView):
    def get(self, *args, **kwargs):
        p = ViewPage(self.request)
        data = p.check_access()
        if data is not None:
            return redirect("{}:missing-rights".format(LinkDatabase.name))

        return super().get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super().get_context_data(**kwargs)
        context = ViewPage(self.request).init_context(context)
        context["page_title"] += " - {}".format(self.get_title())

        return context

    def get_queryset(self):
        p = ViewPage(self.request)
        data = p.check_access()
        if data is not None:
            return redirect("{}:missing-rights".format(LinkDatabase.name))

        return super().get_queryset()

    def get_title(self):
        return ""


class UserGenericListView(GenericListView):
    def get(self, *args, **kwargs):
        p = ViewPage(self.request)
        data = p.check_access()
        if data is not None:
            return redirect("{}:missing-rights".format(LinkDatabase.name))

        self.search_user_id = None
        self.search_user = None

        if "user_id" in kwargs:
            self.search_user_id = kwargs["user_id"]
        if "user" in kwargs:
            self.search_user_id = kwargs["user"]

        if not self.search_user_id or not self.request.user.is_staff:
            self.search_user_id = self.request.user.id

        if self.search_user_id:
            users = User.objects.filter(id=self.search_user_id)
            if users.count() > 0:
                self.search_user = users[0]

        return super().get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super().get_context_data(**kwargs)
        context = ViewPage(self.request).init_context(context)

        return context

    def get_queryset(self):
        p = ViewPage(self.request)
        data = p.check_access()
        if data is not None:
            return redirect("{}:missing-rights".format(LinkDatabase.name))

        if self.search_user:
            return super().get_queryset().filter(user=self.search_user)
        else:
            return super().get_queryset()
