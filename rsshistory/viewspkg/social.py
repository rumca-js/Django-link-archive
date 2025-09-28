from django.views import generic
from django.urls import reverse
from django.shortcuts import redirect
from django.http import HttpResponseRedirect

from ..apps import LinkDatabase
from ..models import SocialData, ConfigurationEntry
from ..controllers import LinkDataController, BackgroundJobController

from ..configuration import Configuration
from ..views import ViewPage, GenericListView
from ..forms import SocialDataForm


def social_data_edit(request, pk):
    p = ViewPage(request)
    p.set_title("Social data")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    entries = LinkDataController.objects.filter(id=pk)
    if not entries.exists():
        p.context["summary_text"] = "No such object"
        return p.render("summary_present.html")

    entry = entries[0]

    socials = SocialData.objects.filter(entry=entry)

    if not socials.exists():
        social = SocialData.objects.create(entry=entry)
    else:
        social = socials[0]

    if request.method == "POST":
        form = SocialDataForm(request.POST, instance=social)
        if form.is_valid():
            form.save()

            return HttpResponseRedirect("{}:entry-detail".format(LinkDatabase.name), args=[social.entry.id])
        else:
            p.context["summary_text"] = "Form is invalid"
            return p.render("summary_present.html")

    form = SocialDataForm(instance=social)
    form.method = "POST"
    form.action_url = reverse(
        "{}:social-data-edit".format(LinkDatabase.name), args=[pk]
    )

    p.context["form"] = form

    return p.render("form_basic.html")


def social_data_update(request, pk):
    p = ViewPage(request)
    p.set_title("Social data update")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    entries = LinkDataController.objects.filter(id=pk)
    if not entries.exists():
        p.context["summary_text"] = "No such object"
        return p.render("summary_present.html")

    entry = entries[0]

    if not SocialData.is_supported(entry):
        p.context["summary_text"] = "Social data not supported"
        return p.render("summary_present.html")

    BackgroundJobController.link_download_social_data(entry=entry)

    p.context["summary_text"] = "OK"
    return p.render("summary_present.html")
