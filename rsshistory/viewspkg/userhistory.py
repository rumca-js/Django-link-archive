from django.views import generic
from django.urls import reverse
from django.shortcuts import redirect
from django.http import HttpResponseRedirect, HttpResponse

from ..apps import LinkDatabase
from ..models import ConfigurationEntry
from ..models import UserEntryVisitHistory
from ..views import ViewPage


class UserEntryVisitHistoryListView(generic.ListView):
    model = UserEntryVisitHistory
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
