from django.shortcuts import redirect
from django.urls import reverse

from ..models import Browser
from ..controllers import (
    LinkDataController,
)
from ..models import ConfigurationEntry, Browser
from ..views import ViewPage, GenericListView
from ..apps import LinkDatabase
from ..forms import BrowserEditForm


class BrowserListView(GenericListView):
    model = Browser
    context_object_name = "content_list"
    paginate_by = 100

    def get_title(self):
        return "Browsers"


def apply_browser_setup(request):
    p = ViewPage(request)
    p.set_title("Clear entire later list")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    Browser.apply_browser_setup()

    p.context["summary_text"] = "OK"
    return p.render("go_back.html")


def read_browser_setup(request):
    p = ViewPage(request)
    p.set_title("Clear entire later list")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    Browser.read_browser_setup()

    p.context["summary_text"] = "OK"
    return p.render("go_back.html")


def remove(request, pk):
    p = ViewPage(request)
    p.set_title("Removes browser")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    browsers = Browser.objects.filter(id=pk)
    if browsers.exists():
        browsers.delete()

        p.context["summary_text"] = "Successfully removed browser"
        return p.render("go_back.html")
    else:
        p.context["summary_text"] = "Cannot find such entry"
        return p.render("go_back.html")


def disable(request, pk):
    p = ViewPage(request)
    p.set_title("Disables browser")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    browsers = Browser.objects.filter(id=pk)
    if browsers.exists():
        browser = browsers[0]
        browser.enabled = False
        browser.save()

        return redirect("{}:browsers".format(LinkDatabase.name))
    else:
        p.context["summary_text"] = "Cannot find such entry"
        return p.render("go_back.html")


def enable(request, pk):
    p = ViewPage(request)
    p.set_title("Enables browser")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    browsers = Browser.objects.filter(id=pk)
    if browsers.exists():
        browser = browsers[0]
        browser.enabled = True
        browser.save()

        return redirect("{}:browsers".format(LinkDatabase.name))
    else:
        p.context["summary_text"] = "Cannot find such entry"
        return p.render("go_back.html")


def edit(request, pk):
    p = ViewPage(request)
    p.set_title("Edit browser")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    browsers = Browser.objects.filter(id=pk)
    if not browsers.exists():
        p.context["summary_text"] = "Could not find such domain"
        return p.render("go_back.html")

    browser = browsers[0]

    if request.method == "POST":
        form = BrowserEditForm(request.POST, instance=browser)
        p.context["form"] = form

        if form.is_valid():
            domain = form.save()

            return redirect("{}:browsers".format(LinkDatabase.name))

        p.context["summary_text"] = "Could not edit domain {}".format(form.cleaned_data)
        return p.render("go_back.html")
    else:
        form = BrowserEditForm(instance=browser)

        form.method = "POST"
        form.action_url = reverse(
            "{}:browser-edit".format(LinkDatabase.name), args=[pk]
        )
        p.context["form"] = form
        return p.render("form_basic.html")
