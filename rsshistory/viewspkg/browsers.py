from django.shortcuts import redirect
from django.http import JsonResponse
from django.urls import reverse

from ..models import Browser
from ..controllers import (
    LinkDataController,
)
from ..models import ConfigurationEntry, Browser
from ..views import ViewPage, SimpleViewPage, GenericListView, get_form_errors
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


def prio_up(request, pk):
    p = SimpleViewPage(request, ConfigurationEntry.ACCESS_TYPE_STAFF)
    if not p.is_allowed():
        return redirect("{}:missing-rights".format(LinkDatabase.name))

    data = {}
    data["message"] = "Entry does not exist"
    data["status"] = False

    browsers = Browser.objects.filter(id=pk)
    if browsers.exists():
        browsers[0].prio_up()
        data["status"] = True
        data["message"] = "OK"

    return JsonResponse(data, json_dumps_params={"indent": 4})


def prio_down(request, pk):
    p = SimpleViewPage(request, ConfigurationEntry.ACCESS_TYPE_STAFF)
    if not p.is_allowed():
        return redirect("{}:missing-rights".format(LinkDatabase.name))

    data = {}
    data["message"] = "Entry does not exist"
    data["status"] = False

    browsers = Browser.objects.filter(id=pk)
    if browsers.exists():
        browsers[0].prio_down()
        data["status"] = True
        data["message"] = "OK"

    return JsonResponse(data, json_dumps_params={"indent": 4})


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


def browser_add(request):
    p = ViewPage(request)
    p.set_title("Add browser")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    if request.method == "POST":
        form = BrowserEditForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(
                reverse("{}:browsers".format(LinkDatabase.name))
            )
        else:
            p.context["summary_text"] = "Form is invalid"
            return p.render("summary_present.html")

    form = BrowserEditForm()
    form.method = "POST"
    form.action_url = reverse("{}:browser-add".format(LinkDatabase.name))

    p.context["form"] = form

    return p.render("form_basic.html")


def edit(request, pk):
    p = ViewPage(request)
    p.set_title("Edit browser")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    browsers = Browser.objects.filter(id=pk)
    if not browsers.exists():
        p.context["summary_text"] = "Could not find such browser"
        return p.render("go_back.html")

    browser = browsers[0]

    if request.method == "POST":
        form = BrowserEditForm(request.POST, instance=browser)
        p.context["form"] = form

        if form.is_valid():
            browser = form.save()

            return redirect("{}:browsers".format(LinkDatabase.name))

        errors = get_form_errors(form)
        p.context["summary_text"] = f"Could not edit browser {errors} {form.cleaned_data}"
        return p.render("go_back.html")
    else:
        form = BrowserEditForm(instance=browser)

        form.method = "POST"
        form.action_url = reverse(
            "{}:browser-edit".format(LinkDatabase.name), args=[pk]
        )
        p.context["form"] = form

        if not browser.is_valid():
            p.context["form_description_post"] = "<b>Browser is not valid</b>"

        return p.render("form_basic.html")
