from django.http import JsonResponse
from django.urls import reverse
from django.core.paginator import Paginator

from ..apps import LinkDatabase
from ..models import (
    ReadLater,
    UserConfig,
)

from ..controllers import (
    LinkDataController,
)
from ..models import ConfigurationEntry
from ..views import ViewPage, UserGenericListView
from ..serializers import entry_to_json


def read_later_entries(request):
    p = ViewPage(request)
    p.set_title("Read later queue")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    data = {}
    if "search" in request.GET:
        data = {"search": request.GET["search"]}

    p.context["query_page"] = reverse(
        "{}:get-read-later-queue".format(LinkDatabase.name)
    )
    p.context["search_suggestions_page"] = None
    p.context["search_history_page"] = None

    return p.render("readlater_list.html")


def read_later_to_json(user_config, read_later):
    entry = read_later.entry

    return entry_to_json(user_config, entry)


def get_read_later_queue(request):
    p = ViewPage(request)
    p.set_title("Read later queue")
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
        objects = ReadLater.objects.filter(user=request.user)

        items_per_page = 100
        p = Paginator(objects, items_per_page)
        page_object = p.page(page_num)

        data["count"] = p.count
        data["num_pages"] = p.num_pages
        user_config = UserConfig.get(request.user)

        if page_num <= p.num_pages:
            for read_later in page_object:
                json_data = read_later_to_json(user_config, read_later)
                data["queue"].append(json_data)

        return JsonResponse(data, json_dumps_params={"indent": 4})


def read_later_add(request, pk):
    p = ViewPage(request)
    p.set_title("Adds to read later")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_LOGGED)
    if data is not None:
        return data

    data = {}

    entries = LinkDataController.objects.filter(id=pk)
    if entries.exists():
        entry = entries[0]

        if ReadLater.objects.filter(entry=entry, user=request.user).count() == 0:
            read_later = ReadLater.objects.create(entry=entry, user=request.user)
            data["message"] = "Added successfully to read queue"
            data["status"] = True
        else:
            data["message"] = "Already in queue"
            data["status"] = True
    else:
        data["message"] = "Cannot find such entry"
        data["status"] = False

    return JsonResponse(data, json_dumps_params={"indent": 4})


def read_later_remove(request, pk):
    p = ViewPage(request)
    p.set_title("Removes entry from read queue list")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_LOGGED)
    if data is not None:
        return data

    data = {}

    entries = LinkDataController.objects.filter(id=pk)
    if entries.exists():
        entry = entries[0]

        read_laters = ReadLater.objects.filter(entry=entry, user=request.user)
        if read_laters.count() > 0:
            read_laters.delete()

            data["message"] = "Successfully removed from read queue"
            data["status"] = True
        else:
            data["message"] = "Cannot find such entry"
            data["status"] = False

    else:
        data["message"] = "Cannot find such entry"
        data["status"] = False
    return JsonResponse(data, json_dumps_params={"indent": 4})


def read_later_clear(request):
    p = ViewPage(request)
    p.set_title("Clear entire later list")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_LOGGED)
    if data is not None:
        return data

    ReadLater.objects.filter(user=request.user).delete()

    data = {}
    data["message"] = "Successfully removed read queue"
    data["status"] = True
    return JsonResponse(data, json_dumps_params={"indent": 4})
