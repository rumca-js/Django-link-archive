from django.urls import reverse
from django.shortcuts import redirect
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.db.models import Q

from ..apps import LinkDatabase
from ..models import (
    ConfigurationEntry,
    BlockEntryList,
    BlockEntry,
    AppLogging,
)
from ..views import ViewPage, GenericListView


def initialize_block_lists(request):
    p = ViewPage(request)
    p.set_title("Initializes block lists")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    BlockEntryList.initialize()

    p.context["summary_text"] = "block lists update OK"

    return p.render("go_back.html")


def block_lists_update(request):
    p = ViewPage(request)
    p.set_title("Update block lists")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    BlockEntryList.update_all()

    p.context["summary_text"] = "Updated lists"

    return p.render("go_back.html")


def block_list_update(request, pk):
    p = ViewPage(request)
    p.set_title("Update block lists")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    thelist = BlockEntryList.objects.filter(id=pk)
    if thelist.exists():
        thelist.update()
        p.context["summary_text"] = "Added block list update job"
    else:
        p.context["summary_text"] = "Could not update block list"

    return p.render("go_back.html")


def block_list_remove(request, pk):
    p = ViewPage(request)
    p.set_title("block list remove")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    thelist = BlockEntryList.objects.filter(id=pk)
    thelist.delete()

    return redirect("{}:block-lists".format(LinkDatabase.name))


def block_lists_clear(request):
    p = ViewPage(request)
    p.set_title("block lists clear")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    BlockEntryList.objects.all().delete()
    BlockEntry.objects.all().delete()

    return redirect("{}:block-lists".format(LinkDatabase.name))


class BlockEntryListListView(GenericListView):
    model = BlockEntryList
    context_object_name = "blocklists"
    paginate_by = 100
    template_name = str(ViewPage.get_full_template("blockentrylist_list.html"))

    def get_title(self):
        return "Block lists"


class BlockEntryListView(GenericListView):
    model = BlockEntry
    context_object_name = "blockentries"
    paginate_by = 100
    template_name = str(ViewPage.get_full_template("blockentry_list.html"))

    def get_title(self):
        return "Block list entries"

    def get_queryset(self):
        if "delete" in self.request.GET and "url" in self.request.GET:
            value = self.request.GET["url"]
            queryset = super().get_queryset().filter(url=value)
            queryset.delete()

        print("BlockEntryListView:get_queryset")
        if "url" in self.request.GET:
            value = self.request.GET["url"]
            return super().get_queryset().filter(url=value)
        else:
            return super().get_queryset()


def blocklists_json(request):
    p = ViewPage(request)
    p.set_title("Block List JSON")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    conditions = Q()
    if "url" in request.GET:
        value = request.GET["url"]
        conditions &= Q(url=value)

    rule_data = []
    for data in BlockEntryList.objects.filter(conditions):
        rule_data.append(model_to_dict(data))

    dict_data = {"blocklists": rule_data}

    return JsonResponse(dict_data, json_dumps_params={"indent": 4})
