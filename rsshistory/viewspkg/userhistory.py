from django.views import generic
from django.urls import reverse
from django.shortcuts import redirect
from django.http import HttpResponseRedirect, HttpResponse

from ..apps import LinkDatabase
from ..models import ConfigurationEntry
from ..models import UserEntryVisitHistory
from ..views import ViewPage, GenericListView


class UserEntryVisitHistoryListView(GenericListView):
    model = UserEntryVisitHistory
    context_object_name = "content_list"
    paginate_by = 100
