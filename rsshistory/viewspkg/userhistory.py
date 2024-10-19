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
