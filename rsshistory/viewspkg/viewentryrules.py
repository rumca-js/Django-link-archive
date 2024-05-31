from django.views import generic
from django.urls import reverse
from django.http import HttpResponseRedirect

from ..apps import LinkDatabase
from ..models import EntryRule
from ..models import ConfigurationEntry
from ..views import ViewPage
from ..forms import EntryRuleForm


class EntryRuleListView(generic.ListView):
    model = EntryRule
    context_object_name = "content_list"
    paginate_by = 100

    def get(self, *args, **kwargs):
        p = ViewPage(self.request)
        data = p.check_access()
        if data:
            return redirect("{}:missing-rights".format(LinkDatabase.name))
        return super().get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super().get_context_data(**kwargs)
        context = ViewPage.init_context(self.request, context)

        return context


class EntryRuleDetailView(generic.DetailView):
    model = EntryRule
    context_object_name = "object_detail"

    def get_context_data(self, **kwargs):
        from ..pluginsources.sourcecontrollerbuilder import SourceControllerBuilder

        # Call the base implementation first to get the context
        context = super().get_context_data(**kwargs)
        context = ViewPage.init_context(self.request, context)

        context["page_title"] += " {} entry rule".format(self.object.rule_name)

        return context


def entry_rule_add(request):
    p = ViewPage(request)
    p.set_title("Add entry rule")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    if request.method == "POST":
        form = EntryRuleForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("{}:entry-rules".format(LinkDatabase.name)))
        else:
            p.context["summary_text"] = "Form is invalid"
            return p.render("summary_present.html")

    form = EntryRuleForm()
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

    objs = EntryRule.objects.filter(id=pk)
    if objs.count() == 0:
        p.context["summary_text"] = "No such object"
        return p.render("summary_present.html")

    if request.method == "POST":
        form = EntryRuleForm(request.POST, instance=objs[0])
        if form.is_valid():
            form.save()
        else:
            p.context["summary_text"] = "Form is invalid"
            return p.render("summary_present.html")

    form = EntryRuleForm(instance=objs[0])
    form.method = "POST"
    form.action_url = reverse(
        "{}:entry-rule-edit".format(LinkDatabase.name), args=[pk]
    )

    p.context["config_form"] = form

    return p.render("configuration.html")


def entry_rule_remove(request, pk):
    p = ViewPage(request)
    p.set_title("Remove data export")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    objs = EntryRule.objects.filter(id=pk)
    if objs.count() == 0:
        p.context["summary_text"] = "No such object"
        return p.render("summary_present.html")
    else:
        objs.delete()
        return HttpResponseRedirect(reverse("{}:entry-rules".format(LinkDatabase.name)))
