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
from ..views import ViewPage, SimpleViewPage, UserGenericListView
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

    p.context["query_page"] = reverse(
        "{}:get-user-browse-history".format(LinkDatabase.name)
    )
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
    p = SimpleViewPage(request, ConfigurationEntry.ACCESS_TYPE_LOGGED)
    if not p.is_allowed():
        return redirect("{}:missing-rights".format(LinkDatabase.name))

    if not request.user.is_authenticated:
        return JsonResponse({}, json_dumps_params={"indent": 4})

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

        return JsonResponse(data, json_dumps_params={"indent": 4})


def history_to_json(history):
    json_obj = {}
    json_obj["search_query"] = history.search_query
    json_obj["date"] = history.date
    json_obj["user_id"] = history.user.id

    return json_obj


def json_user_search_history(request):
    if not request.user.is_authenticated:
        return JsonResponse({}, json_dumps_params={"indent": 4})

    histories = UserSearchHistory.objects.filter(user=request.user).order_by("-date")

    json_obj = {}
    json_obj["histories"] = []

    for history in histories[:50]:
        json_obj["histories"].append(history_to_json(history))

    return JsonResponse(json_obj, json_dumps_params={"indent": 4})


def search_history_remove(request, pk):
    p = SimpleViewPage(request, ConfigurationEntry.ACCESS_TYPE_LOGGED)
    if not p.is_allowed():
        return redirect("{}:missing-rights".format(LinkDatabase.name))

    json_obj = {}

    json_obj["status"] = False

    entries = UserSearchHistory.objects.filter(id=pk)
    if entries.exists():
        json_obj["status"] = True
        entries.delete()

    return JsonResponse(json_obj, json_dumps_params={"indent": 4})


def user_search_history_remove(request, pk):
    p = SimpleViewPage(request, ConfigurationEntry.ACCESS_TYPE_LOGGED)
    if not p.is_allowed():
        return redirect("{}:missing-rights".format(LinkDatabase.name))

    json_obj = {}

    json_obj["status"] = False

    entries = UserSearchHistory.objects.filter(id=pk, user=request.user)
    if entries.exists():
        json_obj["status"] = True
        entries.delete()

    return JsonResponse(json_obj, json_dumps_params={"indent": 4})


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

    if not request.user.is_authenticated:
        return JsonResponse({}, json_dumps_params={"indent": 4})

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

    return JsonResponse(json_obj, json_dumps_params={"indent": 4})


def get_search_suggestions_sources(request, searchstring):
    p = ViewPage(request)
    p.set_title("Search history")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_LOGGED)
    if data is not None:
        return data

    json_obj = {}
    json_obj["items"] = []

    return JsonResponse(json_obj, json_dumps_params={"indent": 4})


def history_remove_all(request):
    p = SimpleViewPage(request, ConfigurationEntry.ACCESS_TYPE_STAFF)
    if not p.is_allowed():
        return redirect("{}:missing-rights".format(LinkDatabase.name))

    json_obj = {}
    json_obj["status"] = True
    json_obj["message"] = ""

    if UserSearchHistory.objects.all().count() > 1000:
        BackgroundJobController.create_single_job("truncate", "UserSearchHistory")
        json_obj["message"] += "Added remove job for UserSearchHistory."
    else:
        UserSearchHistory.objects.all().delete()
        json_obj["message"] += "Removed all entries for UserSearchHistory."

    if UserEntryTransitionHistory.objects.all().count() > 1000:
        BackgroundJobController.create_single_job(
            "truncate", "UserEntryTransitionHistory"
        )
        json_obj["message"] += "Added remove job for UserEntryTransitionHistory."
    else:
        UserEntryTransitionHistory.objects.all().delete()
        json_obj["message"] += "Removed all entries for UserEntryTransitionHistory."

    if UserEntryVisitHistory.objects.all().count() > 1000:
        BackgroundJobController.create_single_job("truncate", "UserEntryVisitHistory")
        json_obj["message"] += "Added remove job for UserEntryVisitHistory."
    else:
        UserEntryVisitHistory.objects.all().delete()
        json_obj["message"] += "Removed all entries for UserEntryVisitHistory."

    return JsonResponse(json_obj, json_dumps_params={"indent": 4})
