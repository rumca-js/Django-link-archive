from django.views import generic
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.urls import reverse

from ..apps import LinkDatabase
from ..models import (
    ConfigurationEntry,
    UserEntryVisitHistory,
    UserSearchHistory,
    SourceCategories,
    SourceSubCategories,
    CompactedTags,
    UserConfig,
)
from ..controllers import SourceDataController
from ..views import ViewPage, UserGenericListView
from ..serializers import entry_to_json


def user_browse_history(request):
    p = ViewPage(request)
    p.set_title("User browse history")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    data = {}
    if "search" in request.GET:
        data = {"search": request.GET["search"]}

    p.context["query_page"] = reverse("{}:get-user-browse-history".format(LinkDatabase.name))
    p.context["search_suggestions_page"] = None
    p.context["search_history_page"] = None

    return p.render("userbrowsehistory_list.html")


def visit_to_json(user_config, visit_data):
    try:
        entry = visit_data.entry
    except Exception as E:
        # if entry was removed?
        visit_data.delete()
        return

    data = entry_to_json(user_config, entry)
    data["date_last_visit"] = visit_data.date_last_visit
    data["number_of_visits"] = visit_data.visits

    return data


def get_user_browse_history(request):
    p = ViewPage(request)
    p.set_title("Get user browse history")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    page_num = p.get_page_num()

    data = {}
    data["queue"] = []
    data["count"] = 0
    data["page"] = page_num
    data["num_pages"] = 0

    if page_num:
        objects = UserEntryVisitHistory.objects.filter(user=request.user)

        items_per_page = 100
        p = Paginator(objects, items_per_page)
        page_object = p.page(page_num)

        data["count"] = p.count
        data["num_pages"] = p.num_pages
        user_config = UserConfig.get(request.user)

        if page_num <= p.num_pages:
            for read_later in page_object:
                json_data = visit_to_json(user_config, read_later)
                data["queue"].append(json_data)

        return JsonResponse(data, json_dumps_params={"indent":4})


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

    for history in histories[:50]:
        json_obj["histories"].append(history_to_json(history))

    return JsonResponse(json_obj, json_dumps_params={"indent":4})


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


def add_suggestion(json_obj, text):
    # if len(json_obj["items"]) > 100:
    #    return

    if text not in json_obj["items"]:
        json_obj["items"].append(text)
        return True


def get_search_suggestions_entries(request, searchstring):
    """
    @note This should not be ignore case - should be blazing fast
    """
    p = ViewPage(request)
    p.set_title("Search history")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_LOGGED)
    if data is not None:
        return data

    json_obj = {}
    json_obj["items"] = []

    suggested_texts = set()

    history_items = UserSearchHistory.objects.filter(
        search_query__contains=searchstring, user=request.user
    )
    for item in history_items:
        text = item.search_query
        add_suggestion(json_obj, text)

    sources = SourceDataController.objects.filter(
        title__contains=searchstring, enabled=True
    )
    for source in sources:
        text = "source__title = '{}'".format(source.title)
        add_suggestion(json_obj, text)

    sources = SourceDataController.objects.filter(
        url__contains=searchstring, enabled=True
    )
    for source in sources:
        text = "source__url = '{}'".format(source.url)
        add_suggestion(json_obj, text)

    categories = SourceCategories.objects.filter(name__contains=searchstring)
    for category in categories:
        text = "category__name = '{}'".format(category.name)
        add_suggestion(json_obj, text)

    subcategories = SourceSubCategories.objects.filter(name__contains=searchstring)
    for subcategory in subcategories:
        text = "subcategory__name = '{}'".format(subcategory.name)
        add_suggestion(json_obj, text)

    tags = CompactedTags.objects.filter(tag__contains=searchstring)[:5]
    for tag in tags:
        text = "tags__tag = '{}'".format(tag.tag)
        add_suggestion(json_obj, text)

    # we do not search entries / links, takes too much time

    # TODO we can search gateways though

    return JsonResponse(json_obj, json_dumps_params={"indent":4})


def get_search_suggestions_sources(request, searchstring):
    p = ViewPage(request)
    p.set_title("Search history")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_LOGGED)
    if data is not None:
        return data

    json_obj = {}
    json_obj["items"] = []

    return JsonResponse(json_obj, json_dumps_params={"indent":4})


def history_remove_all(request):
    p = ViewPage(request)
    p.set_title("Search history")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    UserSearchHistory.objects.all().delete()
    UserEntryTransitionHistory.objects.all().delete()
    UserEntryVisitHistory.objects.all().delete()

    p.context["summary_text"] = "Removed all history objects"
    return p.render("go_back.html")
