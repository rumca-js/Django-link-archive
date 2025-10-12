from pathlib import Path
from urllib.parse import unquote

from django.shortcuts import render, redirect
from django.views import generic
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.http import urlencode

from .models import (
    UserConfig,
    ConfigurationEntry,
    AppLogging,
    ApiKeys,
    Browser,
    SearchView,
)
from .apps import LinkDatabase
from .configuration import Configuration
from .pluginurl.urlhandler import UrlHandlerEx


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
    page = themap.get("page")

    if page:
        try:
            page = int(page)
        except ValueError:
            pass

    if not page:
        page = 1

    return page


def get_request_browser_id(input_map):
    if "browser" in input_map and input_map["browser"] != "":
        return int(input_map["browser"])


def get_request_browser(input_map):
    browser = None

    browser_id = get_request_browser_id(input_map)
    if browser_id is not None:
        if browser_id != Browser.AUTO:
            browsers = Browser.objects.filter(pk=browser_id)
            if browsers.exists():
                browser = browsers[0]
            else:
                AppLogging.error("Browser does not exist!")
                return

    return browser


def get_request_url_with_browser(input_map):
    browser = get_request_browser(input_map)

    if browser:
        browsers = [browser.get_setup()]
    else:
        browsers = None

    page_link = input_map["link"]

    settings = {}
    if "html" in input_map:
        settings["handler_class"] = "HttpPageHandler"  # TODO should not be hardcoded?

    url_ex = UrlHandlerEx(page_link, settings=settings, browsers=browsers)
    return url_ex


def get_search_view(request):
    search_view = None

    if "view" in request.GET:
        search_views = SearchView.objects.filter(id=int(request.GET["view"]))
        if search_views.exists():
            search_view = search_views[0]

    if not search_view:
        search_views = SearchView.objects.filter(default=True)
        if search_views.exists():
            search_view = search_views[0]

    return search_view


class SimpleViewPage(object):
    def __init__(self, request, view_access_type=ConfigurationEntry.ACCESS_TYPE_LOGGED):
        self.request = request
        self.view_access_type = view_access_type

    def printx(self, text):
        pass
        # if self.request:
        #    print("Url:{}: {}".format(self.request.build_absolute_uri(), text))
        # else:
        #    print("{}".format(text))

    def is_allowed(self):
        return self.is_user_allowed_internal(self.view_access_type)

    def is_authenticated(self):
        return self.request.user.is_authenticated

    def check_access(self):
        if not self.is_user_allowed_internal(self.view_access_type):
            return self.render_implementation("missing_rights.html", 500)

    def is_api_key_allowed(self):
        if not self.request:
            return False

        key = self.request.GET.get("key")
        if not key:
            return False

        keys = ApiKeys.objects.filter(key=key)
        if keys.exists():
            return True

    def is_user_allowed_internal(self, view_access_type):
        if self.is_api_key_allowed():
            return True

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

        config_entry = Configuration.get_object().config_entry

        if (
            config_entry.view_access_type == ConfigurationEntry.ACCESS_TYPE_OWNER
            and not self.request.user.is_superuser
        ):
            return False
        if (
            config_entry.view_access_type == ConfigurationEntry.ACCESS_TYPE_STAFF
            and not self.request.user.is_staff
        ):
            return False
        if (
            config_entry.view_access_type == ConfigurationEntry.ACCESS_TYPE_LOGGED
            and not self.request.user.is_authenticated
        ):
            return False

        return True

    def get_pagination_args(self):
        infilters = self.request.GET

        filter_data = {}
        for key in infilters:
            value = infilters[key]
            if key != "page" and value != "":
                filter_data[key] = value
        return "&" + urlencode(filter_data)

    def get_page_num(self):
        page = self.request.GET.get("page")

        if page:
            try:
                page = int(page)
            except ValueError:
                pass

        if not page:
            page = 1

        return page


class ViewPage(SimpleViewPage):
    def __init__(self, request, view_access_type=None):
        super().__init__(request, view_access_type)

        self.printx("ViewPage")

        self.context = None
        self.context = self.get_context()
        self.is_mobile = self.read_mobile_status()
        self.printx("ViewPage DONE")

    def get_context(self, request=None):
        if self.context is not None:
            return self.context

        context = {}
        context = self.init_context(context)

        self.context = context

        return context

    def init_context(self, context):
        self.printx("ViewPage::init_context")

        c = Configuration.get_object()
        config_entry = c.config_entry

        configuration_context = dict(c.get_context())

        configuration_context.update(context)
        context = configuration_context

        if self.is_allowed():
            context["is_user_allowed"] = True

        else:
            context["is_user_allowed"] = False

        context["app_title"] = config_entry.instance_title
        context["app_description"] = config_entry.instance_description
        context["app_favicon"] = config_entry.favicon_internet_url
        if config_entry.admin_user:
            context["admin_email"] = config_entry.admin_user.email
        else:
            context["admin_email"] = ""
        context["admin_user"] = config_entry.admin_user

        if "page_description" not in context:
            if "app_description" in context:
                context["page_description"] = context["app_description"]

        if self.request:
            context["user_config"] = UserConfig.get_or_create(self.request.user)
        else:
            context["user_config"] = UserConfig.get()

        context["config"] = c.config_entry
        context["view"] = self
        self.printx("ViewPage::init_context DONE")

        return context

    def read_mobile_status(self):
        from django_user_agents.utils import get_user_agent

        try:
            user_agent = get_user_agent(self.request)
            return user_agent.is_mobile
        except Exception as E:
            return False

    def get_title(self):
        return "[{}]".format(LinkDatabase.name)

    def set_title(self, title):
        if "page_title" not in self.context:
            self.context["page_title"] = self.get_title()
        if self.context["page_title"] is None:
            self.context["page_title"] = self.get_title()

        if title:
            self.context["page_title"] += " - {}".format(title)

    def set_access(self, view_access_type):
        self.view_access_type = view_access_type

        return self.check_access()

    def set_variable(self, variable_name, variable_value):
        self.context[variable_name] = variable_value

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


class GenericListView(generic.ListView):
    def get(self, *args, **kwargs):
        p = SimpleViewPage(self.request)
        if not p.is_allowed():
            return redirect("{}:missing-rights".format(LinkDatabase.name))

        return super().get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super().get_context_data(**kwargs)
        context = ViewPage(self.request).init_context(context)
        context["page_title"] += " - {}".format(self.get_title())

        return context

    def get_queryset(self):
        p = SimpleViewPage(self.request)
        if not p.is_allowed():
            return redirect("{}:missing-rights".format(LinkDatabase.name))

        return super().get_queryset()

    def get_title(self):
        return ""


class UserGenericListView(GenericListView):
    def get(self, *args, **kwargs):
        self.search_user_id = None
        self.search_user = None

        if self.request.user.is_authenticated:
            self.search_user_id = self.request.user.id
        elif "user_id" in kwargs:
            self.search_user_id = kwargs["user_id"]
        elif "user" in kwargs:
            self.search_user_id = kwargs["user"]

        user = self.get_user()

        return super().get(*args, **kwargs)

    def get_user(self):
        if self.search_user:
            return self.search_user

        if self.search_user_id is None and self.request.user.is_authenticated:
            self.search_user_id = self.request.user.id

        if self.search_user_id:
            users = User.objects.filter(id=self.search_user_id)
            if users.exists():
                self.search_user = users[0]

        return self.search_user

    def get_queryset(self):
        p = SimpleViewPage(self.request)
        if not p.is_allowed():
            return redirect("{}:missing-rights".format(LinkDatabase.name))

        user = self.get_user()

        if user is not None:
            return super().get_queryset().filter(user=user)
        else:
            return super().get_queryset()
