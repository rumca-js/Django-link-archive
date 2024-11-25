from django.urls import reverse
from django.shortcuts import redirect

from ..apps import LinkDatabase
from ..models import (
    ConfigurationEntry,
    BlockEntryList,
    BlockEntry,
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

    p.context["summary_text"] = "Added update block lists job"

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


class BlockEntryListView(GenericListView):
    model = BlockEntry
    context_object_name = "blockentries"
    paginate_by = 100
    template_name = str(ViewPage.get_full_template("blockentry_list.html"))
