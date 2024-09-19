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


def read_later_add(request, pk):
    p = ViewPage(request)
    p.set_title("Adds to read later")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    entries = LinkDataController.objects.filter(id = pk)
    if entries.exists():
        entry = entries[0]

        if ReadLater.objects.filter(entry = entry, user=request.user).count() == 0:
            read_later = ReadLater.objects.create(entry = entry, user=request.user)

            p.context["summary_text"] = "Added successfully to read later queue"
            return p.render("go_back.html")
        else:
            p.context["summary_text"] = "Added successfully to read later queue"
            return p.render("go_back.html")
    else:
        p.context["summary_text"] = "Cannot find such entry"
        return p.render("go_back.html")


def read_later_remove(request, pk):
    p = ViewPage(request)
    p.set_title("Removes entry from read later list")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    read_laters = ReadLater.objects.filter(id = pk, user = request.user)
    if read_laters.exists():
        read_laters.delete()

        p.context["summary_text"] = "Successfully removed from read later list"
        return p.render("go_back.html")
    else:
        p.context["summary_text"] = "Cannot find such entry"
        return p.render("go_back.html")


def read_later_clear(request):
    p = ViewPage(request)
    p.set_title("Clear entire later list")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    read_laters = ReadLater.objects.all().delete()

    p.context["summary_text"] = "Successfully cleared read later list"
    return p.render("go_back.html")
