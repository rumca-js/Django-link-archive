from django.http import JsonResponse

from ..models import ReadLater
from ..controllers import (
    LinkDataController,
)
from ..models import ConfigurationEntry
from ..views import ViewPage, UserGenericListView


class ReadLaterListView(UserGenericListView):
    model = ReadLater
    context_object_name = "content_list"
    paginate_by = 100

    def get_title(self):
        return "Read list"


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
            data["message"] = "Added successfully to read later queue"
            data["status"] = True
            return JsonResponse(data)
        else:
            data["message"] = "Already in queue"
            data["status"] = True
            return JsonResponse(data)
    else:
        data["message"] = "Cannot find such entry"
        data["status"] = False
        return JsonResponse(data)


def read_later_remove(request, pk):
    p = ViewPage(request)
    p.set_title("Removes entry from read later list")
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

            data["message"] = "Successfully removed from read later queue"
            data["status"] = True
            return JsonResponse(data)
        else:
            data["message"] = "Cannot find such entry"
            data["status"] = False
            return JsonResponse(data)

    else:
        data["message"] = "Cannot find such entry"
        data["status"] = False
        return JsonResponse(data)


def read_later_clear(request):
    p = ViewPage(request)
    p.set_title("Clear entire later list")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_LOGGED)
    if data is not None:
        return data

    read_laters = ReadLater.objects.all().delete()

    p.context["summary_text"] = "Successfully cleared read later list"
    return p.render("go_back.html")
