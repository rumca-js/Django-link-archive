from django.views import generic
from django.urls import reverse
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.forms.models import model_to_dict

import random
import string

from ..apps import LinkDatabase
from ..models import ConfigurationEntry
from ..views import ViewPage, GenericListView
from ..models import Credentials
from ..forms import CredentialsForm


class ListView(GenericListView):
    model = Credentials
    context_object_name = "content_list"
    paginate_by = 100

    def get_title(self):
        return "Credentials"


class DetailView(generic.DetailView):
    model = Credentials
    context_object_name = "object"

    def get(self, *args, **kwargs):
        """
        API: Used to redirect if user does not have rights
        """

        p = ViewPage(self.request)
        data = p.check_access()
        if data is not None:
            return redirect("{}:missing-rights".format(LinkDatabase.name))

        view = super().get(*args, **kwargs)
        return view

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super().get_context_data(**kwargs)
        context = ViewPage(self.request).init_context(context)

        context["page_title"] += " {} credential".format(self.object.name)

        return context


def add(request):
    p = ViewPage(request)
    p.set_title("Add credentials")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    if request.method == "POST":
        form = CredentialsForm(request.POST)
        if form.is_valid():
            credentials = form.save(commit=False)
            credentials.encrypt()
            credentials.save()

            return HttpResponseRedirect(
                reverse("{}:credentials".format(LinkDatabase.name))
            )
        else:
            error_message = "\n".join(
                [
                    "{}: {}".format(field, ", ".join(errors))
                    for field, errors in form.errors.items()
                ]
            )

            p.context["summary_text"] = "Could not add credentials {}".format(
                error_message
            )
            return p.render("summary_present.html")

    def random_string(length):
        return "".join(random.choice(string.ascii_letters) for x in range(length))

    form = CredentialsForm()
    form.method = "POST"
    form.action_url = reverse("{}:credential-add".format(LinkDatabase.name))

    p.context["form"] = form

    return p.render("form_basic.html")


def remove(request, pk):
    p = ViewPage(request)
    p.set_title("Remove credentials")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    objs = Credentials.objects.filter(id=pk)
    if objs.count() == 0:
        p.context["summary_text"] = "No such object"
        return p.render("summary_present.html")
    else:
        objs.delete()
        return HttpResponseRedirect(reverse("{}:credentials".format(LinkDatabase.name)))


def edit(request, pk):
    p = ViewPage(request)
    p.set_title("Edit data export")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    objs = Credentials.objects.filter(id=pk)
    if objs.count() == 0:
        p.context["summary_text"] = "No such object"
        return p.render("summary_present.html")

    obj = objs[0]
    obj.secret = obj.decrypt()

    if request.method == "POST":
        form = CredentialsForm(request.POST, instance=obj)
        if form.is_valid():
            credentials = form.save(commit=False)
            credentials.encrypt()
            credentials.save()

            return HttpResponseRedirect(
                reverse("{}:credential".format(LinkDatabase.name), args=[pk])
            )
        else:
            p.context["summary_text"] = "Form is invalid"
            return p.render("summary_present.html")

    form = CredentialsForm(instance=obj)
    form.method = "POST"
    form.action_url = reverse("{}:credential-edit".format(LinkDatabase.name), args=[pk])

    p.context["form"] = form
    return p.render("form_basic.html")
