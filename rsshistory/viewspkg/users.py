from django.views import generic
from django.urls import reverse
from django.shortcuts import redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User

from ..apps import LinkDatabase
from ..models import ConfigurationEntry, UserSearchHistory, UserEntryVisitHistory, UserConfig
from ..controllers import UserCommentsController
from ..views import ViewPage, UserGenericListView, GenericListView


class UserListView(GenericListView):
    model = User
    context_object_name = "content_list"
    paginate_by = 100
    template_name = str(ViewPage.get_full_template("appusers.html"))

    def get_title(self):
        return "User list"


class UserConfigsListView(GenericListView):
    model = UserConfig
    context_object_name = "user_objects"
    paginate_by = 100
    template_name = str(ViewPage.get_full_template("user_configs.html"))

    def get_title(self):
        return "User config list"


class UserEntryVisitHistoryListView(UserGenericListView):
    model = UserEntryVisitHistory
    context_object_name = "content_list"
    paginate_by = 100

    def get_title(self):
        return "User entry visit"


class UserCommentsListView(UserGenericListView):
    model = UserCommentsController
    context_object_name = "content_list"
    paginate_by = 100

    def get_title(self):
        return "User comments"


class UserSearchHistoryListView(UserGenericListView):
    model = UserSearchHistory
    context_object_name = "content_list"
    paginate_by = 100

    def get_title(self):
        return "User search history"


def appuser_history(request, username):
    p = ViewPage(request)
    p.set_title("App user history")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    p.context["summary_text"] = "OK"

    return p.render("summary_present.html")


def user_personal(request):
    p = ViewPage(request)
    p.set_title("User personal view")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    return p.render("user_personal.html")
