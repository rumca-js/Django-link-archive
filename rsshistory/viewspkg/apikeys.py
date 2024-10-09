from django.views import generic
from django.urls import reverse
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.forms.models import model_to_dict

import random
import string

from ..apps import LinkDatabase
from ..models import ConfigurationEntry
from ..views import ViewPage, GenericListView
from ..models import ApiKeys
from ..forms import ApiKeysForm


class ListView(GenericListView):
    model = ApiKeys
    context_object_name = "content_list"
    paginate_by = 100

    def get_title(self):
        return "API Keys"


def add(request):
    p = ViewPage(request)
    p.set_title("Add add rule")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    if request.method == "POST":
        form = ApiKeysForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(
                reverse("{}:api-keys".format(LinkDatabase.name))
            )
        else:
            p.context["summary_text"] = "Form is invalid"
            return p.render("summary_present.html")

    def random_string(length):
        return "".join(random.choice(string.ascii_letters) for x in range(length))

    initial = {
        "key": random_string(20),
    }

    form = ApiKeysForm(initial=initial)
    form.method = "POST"
    form.action_url = reverse("{}:api-key-add".format(LinkDatabase.name))

    p.context["form"] = form

    return p.render("form_basic.html")


def remove(request, pk):
    p = ViewPage(request)
    p.set_title("Remove api key")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    objs = ApiKeys.objects.filter(id=pk)
    if objs.count() == 0:
        p.context["summary_text"] = "No such object"
        return p.render("summary_present.html")
    else:
        objs.delete()
        return HttpResponseRedirect(reverse("{}:api-keys".format(LinkDatabase.name)))
