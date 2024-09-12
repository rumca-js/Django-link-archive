from django.views import generic
from django.urls import reverse
from django.shortcuts import redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User

from ..apps import LinkDatabase
from ..models import ConfigurationEntry
from ..models import UserEntryVisitHistory
from ..views import ViewPage


class UserListView(generic.ListView):
    model = User
    context_object_name = "content_list"
    paginate_by = 100

    def get(self, *args, **kwargs):
        p = ViewPage(self.request)
        data = p.check_access()
        if data is not None:
            return redirect("{}:missing-rights".format(LinkDatabase.name))
        return super().get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super().get_context_data(**kwargs)
        context = ViewPage(self.request).init_context(context)

        return context


class UserEntryVisitHistoryListView(generic.ListView):
    model = UserEntryVisitHistory
    context_object_name = "content_list"
    paginate_by = 100

    def get(self, *args, **kwargs):
        self.search_user_id = None
        self.search_user = None

        if "user_id" in kwargs:
            self.search_user_id = kwargs["user_id"]
            users = User.objects.filter(username = self.search_user_id)
            if users.count() > 0:
                self.search_user = users[0]

        p = ViewPage(self.request)
        data = p.check_access()
        if data is not None:
            return redirect("{}:missing-rights".format(LinkDatabase.name))
        return super().get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super().get_context_data(**kwargs)
        context = ViewPage(self.request).init_context(context)

        return context

    def get_queryset(self):
        """
        API: Returns queryset
        """
        p = ViewPage(self.request)
        data = p.check_access()
        if data is not None:
            return redirect("{}:missing-rights".format(LinkDatabase.name))

        if self.search_user:
            return super().get_queryset().filter(user_object = self.search_user)
        else:
            return super().get_queryset()


def appuser_history(request, username):
    p = ViewPage(request)
    p.set_title("App user history")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    p.context["summary_text"] = "OK"

    return p.render("summary_present.html")
