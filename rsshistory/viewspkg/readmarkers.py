from django.views import generic
from django.urls import reverse
from django.shortcuts import redirect
from django.http import HttpResponseRedirect, HttpResponse

from ..apps import LinkDatabase
from ..models import ConfigurationEntry
from ..models import ReadMarkers
from ..views import ViewPage
from ..controllers import (
    SourceDataController,
)


def set_read_marker(request):
    p = ViewPage(request)
    p.set_title("Sets read marker")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    ReadMarkers.set_general(request.user)

    return redirect("{}:index".format(LinkDatabase.name))


def set_source_read_marker(request, pk):
    p = ViewPage(request)
    p.set_title("Sets read marker")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    source = SourceDataController.objects.get(id = pk)

    ReadMarkers.set_source(request.user, source)

    return redirect("{}:index".format(LinkDatabase.name))
