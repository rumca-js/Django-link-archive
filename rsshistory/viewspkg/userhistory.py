from django.views import generic
from django.urls import reverse
from django.shortcuts import redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.http import JsonResponse

from ..apps import LinkDatabase
from ..models import (
  ConfigurationEntry,
  UserEntryVisitHistory,
  UserSearchHistory,
  SourceCategories,
  SourceSubCategories,
)
from ..controllers import SourceDataController
from ..views import ViewPage, UserGenericListView


class UserEntryVisitHistoryListView(UserGenericListView):
    model = UserEntryVisitHistory
    context_object_name = "content_list"
    paginate_by = 100

    def get_title(self):
        return "User entry visits"


class GetUserSearchHistoryListView(UserGenericListView):
    model = UserSearchHistory
    context_object_name = "search_history"
    paginate_by = 100
    template_name = str(ViewPage.get_full_template("search_history_element.html"))

    def get_title(self):
        return "User search history"

    def get_queryset(self):
        p = ViewPage(self.request)
        data = p.check_access()
        if data is not None:
            return redirect("{}:missing-rights".format(LinkDatabase.name))

        if self.search_user:
            return UserSearchHistory.objects.filter(user=self.search_user).order_by("-date")
        else:
            return UserSearchHistory.objects.all().order_by("-date")


def history_to_json(history):
    json_obj = {}
    json_obj["search_query"] = history.search_query
    json_obj["date"] = history.date
    json_obj["user_id"] = history.user.id

    return json_obj


def json_user_search_history(request):
    histories = UserSearchHistory.objects.filter(user=request.user).order_by("-date")

    json_obj = {}
    json_obj["histories"] = []

    for history in histories:
        json_obj["histories"].append(history_to_json(history))

    return JsonResponse(json_obj)


def search_history_remove(request, pk):
    p = ViewPage(request)
    p.set_title("Remove search history")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_LOGGED)
    if data is not None:
        return data

    entry = UserSearchHistory.objects.get(id=pk)
    entry.delete()

    p.context["summary_text"] = "Removed search from history"
    return p.render("go_back.html")


def get_search_suggestions_entries(request, searchstring):
    p = ViewPage(request)
    p.set_title("Search history")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_LOGGED)
    if data is not None:
        return data

    json_obj = {}
    json_obj["items"] = []

    suggested_texts = set()

    history_items = UserSearchHistory.objects.filter(search_query__contains = searchstring)
    for item in history_items:
        text = item.search_query
        if text not in json_obj["items"]:
            json_obj["items"].append(text)

    sources = SourceDataController.objects.filter(title__contains = searchstring, enabled=True)
    for source in sources:
        text = "source__title = '{}'".format(source.title)
        if text not in json_obj["items"]:
            json_obj["items"].append(text)

    sources = SourceDataController.objects.filter(url__contains = searchstring, enabled=True)
    for source in sources:
        text = "source__url = '{}'".format(source.title)
        if text not in json_obj["items"]:
            json_obj["items"].append(text)

    categories = SourceCategories.objects.filter(name__contains = searchstring)
    for category in categories:
        text = "category__name = '{}'".format(category.name)
        if text not in json_obj["items"]:
            json_obj["items"].append(text)

    subcategories = SourceSubCategories.objects.filter(name__contains = searchstring)
    for subcategory in subcategories:
        text = "subcategory__name = '{}'".format(subcategory.name)
        if text not in json_obj["items"]:
            json_obj["items"].append(text)

    # we could search for link, but this may take too much time?

    return JsonResponse(json_obj)


def get_search_suggestions_sources(request, searchstring):
    p = ViewPage(request)
    p.set_title("Search history")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_LOGGED)
    if data is not None:
        return data

    json_obj = {}
    json_obj["items"] = []

    return JsonResponse(json_obj)
