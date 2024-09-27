from django.views import generic
from django.urls import reverse
from django.shortcuts import redirect
from django.http import HttpResponseRedirect, HttpResponse

from ..apps import LinkDatabase
from ..models import ConfigurationEntry
from ..models import UserEntryVisitHistory, UserSearchHistory
from ..views import ViewPage, UserGenericListView


class UserEntryVisitHistoryListView(UserGenericListView):
    model = UserEntryVisitHistory
    context_object_name = "content_list"
    paginate_by = 100


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
