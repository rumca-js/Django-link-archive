from django.views import generic
from django.urls import reverse
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.forms.models import model_to_dict

from ..apps import LinkDatabase
from ..models import EntryRules, BackgroundJobs, ConfigurationEntry
from ..views import ViewPage, GenericListView
from ..forms import EntryRulesForm


class EntryRulesListView(GenericListView):
    model = EntryRules
    context_object_name = "content_list"
    paginate_by = 100

    def get_title(self):
        return "Entry Rules"


class EntryRulesDetailView(generic.DetailView):
    model = EntryRules
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

        context["page_title"] += " {} entry rule".format(self.object.rule_name)

        return context


def entry_rule_add(request):
    p = ViewPage(request)
    p.set_title("Add entry rule")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    if request.method == "POST":
        form = EntryRulesForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(
                reverse("{}:entry-rules".format(LinkDatabase.name))
            )
        else:
            p.context["summary_text"] = "Form is invalid"
            return p.render("summary_present.html")

    form = EntryRulesForm()
    form.method = "POST"
    form.action_url = reverse("{}:entry-rule-add".format(LinkDatabase.name))

    p.context["form"] = form

    return p.render("form_basic.html")


def entry_rule_edit(request, pk):
    p = ViewPage(request)
    p.set_title("Edit data export")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    objs = EntryRules.objects.filter(id=pk)
    if objs.count() == 0:
        p.context["summary_text"] = "No such object"
        return p.render("summary_present.html")

    if request.method == "POST":
        form = EntryRulesForm(request.POST, instance=objs[0])
        if form.is_valid():
            form.save()
        else:
            p.context["summary_text"] = "Form is invalid"
            return p.render("summary_present.html")

    form = EntryRulesForm(instance=objs[0])
    form.method = "POST"
    form.action_url = reverse("{}:entry-rule-edit".format(LinkDatabase.name), args=[pk])

    p.context["form"] = form
    return p.render("form_basic.html")


def entry_rule_remove(request, pk):
    p = ViewPage(request)
    p.set_title("Remove data export")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    objs = EntryRules.objects.filter(id=pk)
    if objs.count() == 0:
        p.context["summary_text"] = "No such object"
        return p.render("summary_present.html")
    else:
        objs.delete()
        return HttpResponseRedirect(reverse("{}:entry-rules".format(LinkDatabase.name)))


def entry_rule_run(request, pk):
    p = ViewPage(request)
    p.set_title("Remove data export")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    objs = EntryRules.objects.filter(id=pk)
    if objs.count() == 0:
        p.context["summary_text"] = "No such object"
        return p.render("summary_present.html")

    BackgroundJobs.run_rule(objs[0])

    return HttpResponseRedirect(reverse("{}:entry-rules".format(LinkDatabase.name)))


def entry_rules_json(request):
    p = ViewPage(request)
    p.set_title("Entry Rules")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    rule_data = []
    for entry_rule in EntryRules.objects.all():
        rule_data.append(model_to_dict(entry_rule))

    dict_data = {"entryrules": rule_data}

    return JsonResponse(dict_data, json_dumps_params={"indent": 4})
