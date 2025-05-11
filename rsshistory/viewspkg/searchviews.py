"""
"""

from django.views import generic
from django.urls import reverse
from django.http import JsonResponse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.db.models import Q

from ..apps import LinkDatabase
from ..models import (
    SearchView,
    ConfigurationEntry,
)
from ..configuration import Configuration
from ..views import ViewPage, GenericListView
from ..forms import SearchViewForm
from ..queryfilters import DjangoEquationProcessor


class SearchViewListView(GenericListView):
    model = SearchView
    context_object_name = "content_list"
    paginate_by = 100

    def get_title(self):
        return "Search Views"


class SearchViewDetailView(generic.DetailView):
    model = SearchView
    context_object_name = "object_detail"

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

        context["page_title"] += " {} Search view".format(self.object.name)

        return context


def searchviews_initialize(request):
    p = ViewPage(request)
    p.set_title("Searchviews initialization")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    SearchView.reset()

    p.context["summary_text"] = "Initialized searchviews"
    return p.render("go_back.html")


def get_form_condition_errors(form):
    if form.cleaned_data["filter_statement"] != "":
        processor = DjangoEquationProcessor(form.cleaned_data["filter_statement"])
        errors = processor.get_errors()

        if len(errors) > 0:
            return errors


def searchview_edit(request, pk):
    p = ViewPage(request)
    p.set_title("Edit searchview")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    objs = SearchView.objects.filter(id=pk)
    if objs.count() == 0:
        p.context["summary_text"] = "No such object"
        return p.render("go_back.html")

    if request.method == "POST":
        form = SearchViewForm(request.POST, instance=objs[0])
        errors = get_form_condition_errors(form)

        if objs[0].default and not form.cleaned_data["default"]:
            p.context["summary_text"] = "Cannot disable default view!"
            return p.render("go_back.html")

        elif errors and len(errors) > 0:
            error_message = "\n".join(errors)
            p.context["summary_text"] = "Form is invalid: {}".format(error_message)
            return p.render("summary_present.html")

        elif form.is_valid():
            form.save()

            return HttpResponseRedirect(
                reverse("{}:searchview".format(LinkDatabase.name), args=[pk])
            )
        else:
            p.context["summary_text"] = "Form is invalid"
            return p.render("summary_present.html")

    form = SearchViewForm(instance=objs[0])
    form.method = "POST"
    form.action_url = reverse("{}:searchview-edit".format(LinkDatabase.name), args=[pk])

    p.context["form"] = form
    return p.render("form_basic.html")


def searchview_add(request):
    p = ViewPage(request)
    p.set_title("Add search view")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    if request.method == "POST":
        form = SearchViewForm(request.POST)
        errors = get_form_condition_errors(form)

        if errors and len(errors) > 0:
            error_message = "\n".join(errors)
            p.context["summary_text"] = "Form is invalid: {}".format(error_message)
            return p.render("summary_present.html")

        elif form.is_valid():
            form.save()
            return HttpResponseRedirect(
                reverse("{}:searchviews".format(LinkDatabase.name))
            )

        else:
            error_message = "\n".join(
                [
                    "{}: {}".format(field, ", ".join(errors))
                    for field, errors in form.errors.items()
                ]
            )

            p.context["summary_text"] = "Form is invalid: {}".format(error_message)
            return p.render("summary_present.html")

    form = SearchViewForm()
    form.method = "POST"
    form.action_url = reverse("{}:searchview-add".format(LinkDatabase.name))

    p.context["form"] = form
    return p.render("form_basic.html")


def searchview_remove(request, pk):
    p = ViewPage(request)
    p.set_title("Remove search view")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    objs = DataExport.objects.filter(id=pk)
    if objs.count() == 0:
        p.context["summary_text"] = "No such object"
        return p.render("go_back.html")
    else:
        if objs[0].default:
            p.context["summary_text"] = "Cannot remove default view!"
            return p.render("go_back.html")
        else:
            objs.delete()

            return redirect("{}:searchviews".format(LinkDatabase.name))
